import json
from pathlib import Path

import pytest
from hydra_umc_developer_node import approvals, panel, plugin_ci
from hydra_umc_developer_node.schema import validate
from hydra_umc_developer_node.store import Store
from support import make_bundle, settings

NOW = 9_000.0


def panel_settings(tmp_path: Path, **extra: object) -> object:
    return settings(dataDir=str(tmp_path / "data"), panel={"enabled": True, "maxJournalEntries": 3}, language="de", **extra)


def test_the_panel_is_closed_by_default(tmp_path: Path) -> None:
    with Store(tmp_path / "s.db") as store, pytest.raises(panel.PanelError, match="closed"):
        panel.build_status(settings(dataDir=str(tmp_path)), store)


def test_status_follows_the_contract_and_counts_the_queue(tmp_path: Path) -> None:
    config = panel_settings(tmp_path)
    with Store(tmp_path / "s.db") as store:
        store.add_case("a", "file", make_bundle(), NOW)
        store.add_case("b", "file", make_bundle(impact="other"), NOW)
        store.set_status("b", "reviewed")
        for index in range(5):
            store.log("note", f"entry {index}", "a", NOW + index)
        approvals.approve(store, "a", "repro-run", "c" * 64, prompt=lambda _t: "c" * 8, approver="p", now=NOW)
        status = panel.build_status(config, store, NOW + 10)  # type: ignore[arg-type]
    validate("panel_status", status)
    assert status["queue"]["cases"] == {"awaiting-review": 1, "reviewed": 1}
    assert status["queue"]["awaiting_approval"] == 1
    assert len(status["journal"]) == 3 and status["journal"][0]["detail"] and status["journal"][0]["id"] > status["journal"][1]["id"]
    assert status["language"] == "de" and status["labels"]["title"] == "Entwicklungsknoten"
    assert status["switches"]["panel"] is True and status["switches"]["ingest"] is False
    assert status["health"]["store_ok"] is True and status["health"]["cache_over_limit"] is False


def test_status_never_carries_a_bundle_or_a_recipe(tmp_path: Path) -> None:
    with Store(tmp_path / "s.db") as store:
        store.add_case("a", "file", make_bundle(impact="the-private-impact-text"), NOW)
        text = json.dumps(panel.build_status(panel_settings(tmp_path), store, NOW))  # type: ignore[arg-type]
    assert "the-private-impact-text" not in text


def test_export_writes_one_file_atomically(tmp_path: Path) -> None:
    config = panel_settings(tmp_path)
    with Store(tmp_path / "s.db") as store:
        path = panel.export_status(config, store, NOW)  # type: ignore[arg-type]
    assert path.name == "status.json" and not (path.parent / "status.json.tmp").exists()
    validate("panel_status", json.loads(path.read_text(encoding="utf-8")))


def make_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "ws"
    for name, code in (("good", 0), ("bad", 3)):
        (workspace / name / "tools").mkdir(parents=True, exist_ok=True)
        (workspace / name / "tools" / "ci_validate.py").write_text(
            f"import os, sys\nprint('CI_VALIDATION=' + ('PASS' if {code} == 0 else 'FAIL'))\nprint('flag', os.environ.get('HYDRA_UMC_CI'))\n"
            f"print('password=hunter2hunter2')\nsys.exit({code})\n", encoding="utf-8")
    (workspace / "empty").mkdir(exist_ok=True)
    return workspace


def ci_settings(tmp_path: Path, **kw: object):  # type: ignore[no-untyped-def]
    section = {"enabled": True, "workspace": str(make_workspace(tmp_path)), "repos": ["good", "bad", "empty"], "tailLines": 5}
    section.update(kw)
    return settings(dataDir=str(tmp_path / "data"), ecosystemCi=section)


def test_the_plugin_is_closed_and_needs_an_exact_approval(tmp_path: Path) -> None:
    config = ci_settings(tmp_path, enabled=False)
    plan = plugin_ci.build_plan(config.ecosystem_ci)
    with Store(tmp_path / "s.db") as store:
        with pytest.raises(plugin_ci.PluginError, match="closed"):
            plugin_ci.run(plan, store, config.ecosystem_ci, config.data_path())
        config = ci_settings(tmp_path)
        plan = plugin_ci.build_plan(config.ecosystem_ci)
        with pytest.raises(plugin_ci.PluginError, match="approval"):
            plugin_ci.run(plan, store, config.ecosystem_ci, config.data_path())
        assert not (config.data_path() / "ci-reports").exists()


def test_the_report_is_consolidated_redacted_and_saved(tmp_path: Path) -> None:
    config = ci_settings(tmp_path)
    plan = plugin_ci.build_plan(config.ecosystem_ci)
    digest = plugin_ci.plan_digest(plan)
    with Store(tmp_path / "s.db") as store:
        approvals.approve(store, plugin_ci.SUBJECT, plugin_ci.ACTION, digest, prompt=lambda _t: digest[:8], approver="p", now=NOW)
        report = plugin_ci.run(plan, store, config.ecosystem_ci, config.data_path(), NOW)
        with pytest.raises(plugin_ci.PluginError, match="approval"):  # single use
            plugin_ci.run(plan, store, config.ecosystem_ci, config.data_path(), NOW)
        status = panel.build_status(settings(dataDir=str(config.data_path()), panel={"enabled": True}), store, NOW)
    by_repo = {item["repo"]: item for item in report["results"]}
    assert [by_repo[name]["status"] for name in ("good", "bad", "empty")] == ["pass", "fail", "skipped"]
    assert by_repo["good"]["tail"][1] == "flag 1"
    assert "hunter2" not in json.dumps(report)
    assert report["summary"] == {"pass": 1, "fail": 1, "error": 0, "skipped": 1}
    validate("ecosystem_ci_report", report)
    assert plugin_ci.latest_report(config.data_path()) == report
    assert status["health"]["last_ci_report"]["summary"]["fail"] == 1


def test_a_changed_plan_is_not_the_approved_one(tmp_path: Path) -> None:
    config = ci_settings(tmp_path)
    plan = plugin_ci.build_plan(config.ecosystem_ci)
    plan["repos"] = ["good", "bad", "empty", "extra"]
    with Store(tmp_path / "s.db") as store, pytest.raises(plugin_ci.PluginError, match="not the one"):
        plugin_ci.run(plan, store, config.ecosystem_ci, config.data_path())


def test_the_plan_refuses_paths_and_empty_lists(tmp_path: Path) -> None:
    for repos in (["../x"], ["a/b"], ["a\\b"], [".."]):
        with pytest.raises(plugin_ci.PluginError):
            plugin_ci.build_plan(ci_settings(tmp_path, repos=repos).ecosystem_ci)
    with pytest.raises(plugin_ci.PluginError, match="repos"):
        plugin_ci.build_plan(ci_settings(tmp_path, repos=[]).ecosystem_ci)
    with pytest.raises(plugin_ci.PluginError, match="workspace"):
        plugin_ci.build_plan(ci_settings(tmp_path, workspace="").ecosystem_ci)


def test_a_timeout_is_an_error_of_that_repository(tmp_path: Path) -> None:
    config = ci_settings(tmp_path, repos=["slow"], timeoutSeconds=1)
    folder = Path(config.ecosystem_ci.workspace) / "slow" / "tools"
    folder.mkdir(parents=True)
    (folder / "ci_validate.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    plan = plugin_ci.build_plan(config.ecosystem_ci)
    digest = plugin_ci.plan_digest(plan)
    with Store(tmp_path / "s.db") as store:
        approvals.approve(store, plugin_ci.SUBJECT, plugin_ci.ACTION, digest, prompt=lambda _t: digest[:8], approver="p", now=NOW)
        report = plugin_ci.run(plan, store, config.ecosystem_ci, config.data_path(), NOW)
    assert report["results"][0]["status"] == "error"
