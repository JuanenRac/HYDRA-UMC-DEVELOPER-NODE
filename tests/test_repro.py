import sys
from pathlib import Path
from typing import Any

import pytest
from hydra_umc_developer_node import approvals, repro
from hydra_umc_developer_node.schema import validate
from hydra_umc_developer_node.settings import ReproSettings
from hydra_umc_developer_node.store import Store
from support import PY, make_bundle

NOW = 5_000.0


def recipe(code: int = 3, extra_steps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    probe = {"argv": [sys.executable, "-c", f"import sys; print('probe'); sys.exit({code})"]}
    return {"schema_version": "1.0", "scenario_id": "demo/probe", "repro_case": "exit-code",
            "steps": [*(extra_steps or []), probe], "reproduced_when": {"exit_code_not": 0}}


def open_settings(**kw: object) -> ReproSettings:
    options: dict[str, object] = {"enabled": True, "allowed_commands": (PY,)}
    options.update(kw)
    return ReproSettings(**options)  # type: ignore[arg-type]


def prepared(tmp_path: Path) -> tuple[Store, Path]:
    store = Store(tmp_path / "s.db")
    store.add_case("c1", "file", make_bundle(), NOW)
    work = tmp_path / "work"
    work.mkdir()
    return store, work


def approve(store: Store, document: dict[str, Any], when: float = NOW) -> None:
    digest = approvals.digest_of(document)
    approvals.approve(store, "c1", repro.ACTION, digest, prompt=lambda _text: digest[:8], approver="tester", now=when)


def test_nothing_runs_while_the_switch_is_closed(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    with pytest.raises(repro.ReproError, match="closed"):
        repro.run_recipe(recipe(), store, ReproSettings(), "c1", "before", work, "sha-a", NOW)


def test_nothing_runs_without_an_approval(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    with pytest.raises(repro.ReproError, match="approval"):
        repro.run_recipe(recipe(), store, open_settings(), "c1", "before", work, "sha-a", NOW)
    assert store.outcome_count() == 0


def test_an_approval_is_for_the_exact_recipe_and_single_use(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    approve(store, recipe(3))
    with pytest.raises(repro.ReproError, match="approval"):
        repro.run_recipe(recipe(4), store, open_settings(), "c1", "before", work, "sha-a", NOW)
    repro.run_recipe(recipe(3), store, open_settings(), "c1", "before", work, "sha-a", NOW + 1)
    with pytest.raises(repro.ReproError, match="approval"):
        repro.run_recipe(recipe(3), store, open_settings(), "c1", "before", work, "sha-a", NOW + 2)


def test_an_approval_expires(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    approve(store, recipe())
    with pytest.raises(repro.ReproError, match="approval"):
        repro.run_recipe(recipe(), store, open_settings(approval_max_age_minutes=1), "c1", "before", work, "sha-a", NOW + 61)


def test_approval_needs_a_person_and_the_right_confirmation(tmp_path: Path) -> None:
    store, _ = prepared(tmp_path)

    class NoTerminal:
        def isatty(self) -> bool:
            return False

    with pytest.raises(approvals.ApprovalError, match="terminal"):
        approvals.approve(store, "c1", repro.ACTION, "a" * 64, stream=NoTerminal())  # type: ignore[arg-type]
    for typed in ("", "bbbbbbbb", "aaaaaaa"):
        with pytest.raises(approvals.ApprovalError, match="confirmation"):
            approvals.approve(store, "c1", repro.ACTION, "a" * 64, prompt=lambda _t, typed=typed: typed)  # type: ignore[misc]
    assert store.pending_approvals(3600, NOW) == 0


def test_a_run_that_reproduces_and_one_that_does_not(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    approve(store, recipe(3))
    broken = repro.run_recipe(recipe(3), store, open_settings(), "c1", "before", work, "sha-a", NOW)
    assert broken["observed"] == {"outcome": "reproduced", "exit_code": 3, "evidence": broken["observed"]["evidence"]}
    assert "probe" in broken["observed"]["evidence"]
    validate("scenario-outcome", broken)
    approve(store, recipe(0))
    fixed = repro.run_recipe(recipe(0), store, open_settings(), "c1", "after", work, "sha-b", NOW)
    assert fixed["observed"]["outcome"] == "not-reproduced"
    assert store.outcome_count() == 2


def test_a_command_outside_the_allow_list_is_refused_before_anything_starts(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    document = recipe()
    document["steps"][0]["argv"] = ["definitely-not-allowed", "--x"]
    approve(store, document)
    with pytest.raises(repro.ReproError, match="allowedCommands"):
        repro.run_recipe(document, store, open_settings(), "c1", "before", work, "sha-a", NOW)
    assert store.pending_approvals(3600, NOW) == 1  # the approval was not used up
    with pytest.raises(repro.ReproError):
        repro.check_recipe(document, ReproSettings())  # an empty allow-list allows nothing


def test_a_failing_preparation_step_is_an_error_not_a_reproduction(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    document = recipe(extra_steps=[{"argv": [sys.executable, "-c", "import sys; sys.exit(9)"]}])
    approve(store, document)
    outcome = repro.run_recipe(document, store, open_settings(), "c1", "before", work, "sha-a", NOW)
    assert outcome["observed"]["outcome"] == "error" and "preparation step 1" in outcome["observed"]["evidence"]


def test_a_timeout_is_an_error(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    document = recipe()
    document["steps"][0]["argv"] = [sys.executable, "-c", "import time; time.sleep(30)"]
    approve(store, document)
    outcome = repro.run_recipe(document, store, open_settings(step_timeout_seconds=1), "c1", "before", work, "sha-a", NOW)
    assert outcome["observed"]["outcome"] == "error"


def test_output_is_redacted_and_bounded(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    document = recipe()
    document["steps"][0]["argv"] = [sys.executable, "-c", "print('password=hunter2hunter2'); print('x' * 500)"]
    approve(store, document)
    outcome = repro.run_recipe(document, store, open_settings(max_output_bytes=100), "c1", "before", work, "sha-a", NOW)
    assert "hunter2" not in outcome["observed"]["evidence"] and len(outcome["observed"]["evidence"]) <= 100


def test_the_step_folder_must_stay_inside_the_checkout(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    for cwd in ("..", "/etc", "a/../.."):
        document = recipe()
        document["steps"][0]["cwd"] = cwd
        with pytest.raises(repro.ReproError, match="relative"):
            repro.check_recipe(document, open_settings())
    (work / "sub").mkdir()
    document = recipe()
    document["steps"][0]["cwd"] = "sub"
    approve(store, document)
    assert repro.run_recipe(document, store, open_settings(), "c1", "before", work, "sha-a", NOW)["observed"]["outcome"] == "reproduced"


def test_the_environment_of_a_step_is_minimal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_SECRET_TOKEN_FOR_TEST", "should-not-pass")
    store, work = prepared(tmp_path)
    document = recipe()
    document["steps"][0]["argv"] = [sys.executable, "-c", "import os; print('LEAK' if 'MY_SECRET_TOKEN_FOR_TEST' in os.environ else 'CLEAN')"]
    approve(store, document)
    outcome = repro.run_recipe(document, store, open_settings(), "c1", "before", work, "sha-a", NOW)
    assert "CLEAN" in outcome["observed"]["evidence"]


def test_limits_of_the_recipe_and_the_run(tmp_path: Path) -> None:
    store, work = prepared(tmp_path)
    with pytest.raises(repro.ReproError, match="maxSteps"):
        repro.check_recipe(recipe(extra_steps=[{"argv": [sys.executable, "-c", "pass"]}] * 3), open_settings(max_steps=2))
    with pytest.raises(repro.ReproError, match="phase"):
        repro.run_recipe(recipe(), store, open_settings(), "c1", "during", work, "sha-a", NOW)
    with pytest.raises(repro.ReproError, match="fingerprint"):
        repro.run_recipe(recipe(), store, open_settings(), "c1", "before", work, "", NOW)
    with pytest.raises(repro.ReproError, match="does not exist"):
        repro.run_recipe(recipe(), store, open_settings(), "c1", "before", tmp_path / "none", "sha-a", NOW)
    with pytest.raises(Exception, match="unknown case"):
        repro.run_recipe(recipe(), store, open_settings(), "nope", "before", work, "sha-a", NOW)


def test_load_recipe_errors(tmp_path: Path) -> None:
    with pytest.raises(repro.ReproError, match="cannot read"):
        repro.load_recipe(tmp_path / "none.json", open_settings())
    (tmp_path / "bad.json").write_text("{")
    with pytest.raises(repro.ReproError, match="JSON"):
        repro.load_recipe(tmp_path / "bad.json", open_settings())
    (tmp_path / "wrong.json").write_text("{}")
    with pytest.raises(repro.ReproError, match="ReproRecipe"):
        repro.load_recipe(tmp_path / "wrong.json", open_settings())


def test_the_verdict_is_computed_by_the_sdk_not_by_this_repository(tmp_path: Path) -> None:
    pytest.importorskip("hydra_umc_sdk")
    store, work = prepared(tmp_path)
    approve(store, recipe(3))
    repro.run_recipe(recipe(3), store, open_settings(), "c1", "before", work, "sha-a", NOW)
    approve(store, recipe(0))
    repro.run_recipe(recipe(0), store, open_settings(), "c1", "after", work, "sha-b", NOW)
    assert repro.compare(store, "c1", "demo/probe")["verdict"] == "regression-fixed"
    approve(store, recipe(0))
    repro.run_recipe(recipe(0), store, open_settings(), "c1", "after", work, "sha-a", NOW)  # same fingerprint: nothing was applied
    assert repro.compare(store, "c1", "demo/probe")["verdict"] == "apparent-success"


def test_compare_needs_both_runs_and_says_so_without_the_sdk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, _ = prepared(tmp_path)
    with pytest.raises(repro.ReproError, match="both"):
        repro.compare(store, "c1", "demo/probe")
    for phase in ("before", "after"):
        store.add_outcome("c1", {"scenario_id": "s", "phase": phase, "run_id": phase})
    monkeypatch.setitem(sys.modules, "hydra_umc_sdk", None)
    monkeypatch.setitem(sys.modules, "hydra_umc_sdk.scenario", None)
    with pytest.raises(repro.ReproError, match="sdk"):
        repro.compare(store, "c1", "s")
