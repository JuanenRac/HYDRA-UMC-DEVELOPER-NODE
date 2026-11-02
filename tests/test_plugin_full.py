import json
from typing import Any
import time
from pathlib import Path

import pytest
from hydra_umc_developer_node import approvals, cli, panel, plugin_ci, plugin_full
from hydra_umc_developer_node.schema import validate
from hydra_umc_developer_node.settings import Settings
from hydra_umc_developer_node.store import Store
from support import settings

NOW = 50_000.0
OK = "print('ok')\n"


def make_repo(workspace: Path, name: str, ci: str | None = OK, test: str | None = OK, manifest: dict[str, Any] | None = None) -> None:
    folder = workspace / name
    (folder / "tools").mkdir(parents=True, exist_ok=True)
    if ci is not None:
        (folder / "tools" / "ci_validate.py").write_text(ci, encoding="utf-8")
    if test is not None:
        (folder / "tools" / "build_test.py").write_text(test, encoding="utf-8")
        declared = {"developer_node": {"full_test": {"interpreter": "python", "script": "tools/build_test.py"}}}
        (folder / "hydra-umc.project.json").write_text(json.dumps(manifest if manifest is not None else declared), encoding="utf-8")


def config(tmp_path: Path, repos: list[str], full: dict[str, object] | None = None, ci: dict[str, object] | None = None) -> Settings:
    section: dict[str, object] = {"enabled": True, "workspace": str(tmp_path / "ws"), "repos": repos}
    section.update(ci or {})
    options: dict[str, object] = {"enabled": True, "minFreeGb": 0.001, "perRepoTimeoutSeconds": 20}
    options.update(full or {})
    return settings(dataDir=str(tmp_path / "data"), ecosystemCi=section, ecosystemCiFull=options)


def approve(store: Store, plan: dict[str, object], at: float = NOW) -> str:
    digest = plugin_full.plan_digest(plan)
    approvals.approve(store, plugin_full.SUBJECT, plugin_full.ACTION, digest, prompt=lambda _t: digest[:8], approver="p", now=at)
    return digest


def run_plan(tmp_path: Path, cfg: Settings, exclude: tuple[str, ...] = (), **kw: object) -> dict[str, object]:
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full, exclude)
    with Store(tmp_path / "s.db") as store:
        approve(store, plan)
        return plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), exclude, NOW, **kw)  # type: ignore[arg-type]


def by_command(report: dict[str, object], repo: str) -> dict[str, dict[str, object]]:
    return {("ci" if "ci_validate" in item["command"] else "full"): item for item in report["results"] if item["repo"] == repo}  # type: ignore[index,attr-defined]


def test_it_is_closed_by_default_and_needs_both_switches(tmp_path: Path) -> None:
    make_repo(tmp_path / "ws", "a")
    plan = plugin_full.build_plan(config(tmp_path, ["a"]).ecosystem_ci, config(tmp_path, ["a"]).ecosystem_ci_full)
    with Store(tmp_path / "s.db") as store:
        for cfg, word in ((config(tmp_path, ["a"], full={"enabled": False}), "ecosystemCiFull is closed"),
                          (config(tmp_path, ["a"], ci={"enabled": False}), "ecosystemCi is closed")):
            with pytest.raises(plugin_ci.PluginError, match=word):
                plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path())
    assert Settings().ecosystem_ci_full.enabled is False and Settings().switches()["ecosystemCiFull"] is False


def test_the_plan_lists_each_command_and_runs_nothing_that_is_not_declared(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    make_repo(ws, "declared")
    make_repo(ws, "only-ci", test=None)
    make_repo(ws, "nothing", ci=None, test=None)
    make_repo(ws, "bad-path", test=OK, manifest={"developer_node": {"full_test": {"interpreter": "python", "script": "../x.py"}}})
    make_repo(ws, "bad-shell", test=OK, manifest={"developer_node": {"full_test": {"interpreter": "bash -c", "script": "tools/build_test.py"}}})
    cfg = config(tmp_path, ["declared", "only-ci", "nothing", "bad-path", "bad-shell"])
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full)
    commands = {item["repo"]: [c["id"] for c in item["commands"]] for item in plan["repos"]}
    assert commands == {"declared": ["ci_validate", "full_test"], "only-ci": ["ci_validate"], "nothing": [], "bad-path": ["ci_validate"],
                        "bad-shell": ["ci_validate"]}
    assert all(len(c["script_sha256"]) == 64 for item in plan["repos"] for c in item["commands"])
    text = "\n".join(plugin_full.describe(plan))
    assert "nothing: nothing will run" in text and "declared:" in text
    report = run_plan(tmp_path, cfg)
    nothing = [item for item in report["results"] if item["repo"] == "nothing"]  # type: ignore[attr-defined]
    assert len(nothing) == 1 and nothing[0]["status"] == "skipped" and nothing[0]["command"] == ""
    assert report["summary"] == {"pass": 5, "fail": 0, "timeout": 0, "skipped": 1}
    validate("ecosystem_ci_full_report", report)
    assert plugin_full.exit_code(report) == 0  # type: ignore[arg-type]


def test_exclusion_removes_the_repository_from_the_plan_and_the_run(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    make_repo(ws, "a")
    make_repo(ws, "b", test="raise SystemExit(7)\n")
    cfg = config(tmp_path, ["a", "b"])
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full, ("b",))
    assert [item["repo"] for item in plan["repos"]] == ["a"] and plan["excluded"] == ["b"]
    assert plugin_full.plan_digest(plan) != plugin_full.plan_digest(plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full))
    report = run_plan(tmp_path, cfg, ("b",))
    assert {item["repo"] for item in report["results"]} == {"a"}  # type: ignore[attr-defined]
    with pytest.raises(plugin_ci.PluginError, match="cannot exclude"):
        plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full, ("zzz",))
    with pytest.raises(plugin_ci.PluginError, match="excluded"):
        plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full, ("a", "b"))


def test_a_plan_without_approval_or_with_an_approval_of_another_plan_runs_nothing(tmp_path: Path) -> None:
    marker = (tmp_path / "marker").as_posix()
    make_repo(tmp_path / "ws", "a", test=f"open(r'{marker}', 'w').write('ran')\n")
    cfg = config(tmp_path, ["a"])
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full)
    with Store(tmp_path / "s.db") as store:
        with pytest.raises(plugin_ci.PluginError, match="approval"):
            plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW)
        approve(store, {**plan, "excluded": ["x"]})  # a digest of a different plan
        with pytest.raises(plugin_ci.PluginError, match="approval"):
            plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW)
    assert not (tmp_path / "marker").exists()


def test_an_expired_approval_is_refused_and_a_valid_one_is_single_use(tmp_path: Path) -> None:
    make_repo(tmp_path / "ws", "a")
    cfg = config(tmp_path, ["a"], full={"approvalMaxAgeMinutes": 5})
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full)
    with Store(tmp_path / "s.db") as store:
        approve(store, plan, NOW)
        with pytest.raises(plugin_ci.PluginError, match="approval"):
            plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW + 5 * 60 + 1)
        approve(store, plan, NOW + 400)
        plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW + 401)
        with pytest.raises(plugin_ci.PluginError, match="approval"):
            plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW + 402)


def test_an_altered_plan_or_a_script_changed_after_approval_does_not_run(tmp_path: Path) -> None:
    make_repo(tmp_path / "ws", "a")
    cfg = config(tmp_path, ["a"])
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full)
    tampered = json.loads(json.dumps(plan))
    tampered["repos"][0]["commands"][1]["argv"] = ["sh", "-c", "evil"]
    with Store(tmp_path / "s.db") as store:
        approve(store, plan)
        with pytest.raises(plugin_ci.PluginError, match="not the one"):
            plugin_full.run(tampered, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW)
        (tmp_path / "ws" / "a" / "tools" / "build_test.py").write_text("print('changed')\n", encoding="utf-8")
        with pytest.raises(plugin_ci.PluginError, match="not the one"):
            plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW)


def test_a_timeout_stops_that_command_and_the_batch_goes_on(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    make_repo(ws, "slow", test="import time\ntime.sleep(60)\n")
    make_repo(ws, "fast")
    cfg = config(tmp_path, ["slow", "fast"], full={"perRepoTimeoutSeconds": 1})
    started = time.monotonic()
    report = run_plan(tmp_path, cfg)
    assert time.monotonic() - started < 30
    slow, fast = by_command(report, "slow"), by_command(report, "fast")
    assert slow["ci"]["status"] == "pass" and slow["full"]["status"] == "timeout" and slow["full"]["exit_code"] is None
    assert fast["full"]["status"] == "pass"
    assert report["summary"]["timeout"] == 1 and plugin_full.exit_code(report) == 1  # type: ignore[arg-type,index]


def test_the_total_time_limit_skips_what_is_left(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    make_repo(ws, "slow", test="import time\ntime.sleep(60)\n")
    make_repo(ws, "later")
    cfg = config(tmp_path, ["slow", "later"], full={"totalTimeoutSeconds": 2, "includeCiValidate": False})
    report = run_plan(tmp_path, cfg)
    assert by_command(report, "slow")["full"]["status"] == "timeout"
    assert report["aborted"] == "total_timeout"
    assert by_command(report, "later")["full"]["status"] == "skipped" and plugin_full.exit_code(report) == 1  # type: ignore[arg-type]


def test_huge_output_is_cut_and_bounded(tmp_path: Path) -> None:
    make_repo(tmp_path / "ws", "noisy", test="import sys\nwhile True:\n    sys.stdout.write('x' * 1000 + '\\n')\n")
    cfg = config(tmp_path, ["noisy"], full={"maxOutputBytes": 20000, "tailLines": 3, "includeCiValidate": False})
    report = run_plan(tmp_path, cfg)
    item = report["results"][0]  # type: ignore[index]
    assert item["status"] == "fail" and "output limit" in item["note"]
    assert len(item["tail"]) <= 3 and all(len(line) <= plugin_full.MAX_LINE for line in item["tail"])
    assert len(json.dumps(report)) < 5000


def test_output_summary_is_redacted_and_the_environment_is_minimal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_API_TOKEN", "sekret-value-123")
    monkeypatch.setenv("UNRELATED_VAR", "visible-unrelated")
    monkeypatch.setenv("KEEP_ME", "kept-value")
    code = ("import os\nprint('password=hunter2hunter2')\n"
            "print('keys', sorted(k for k in os.environ if k in ('MY_API_TOKEN','UNRELATED_VAR','KEEP_ME')))\n"
            "print('ci', os.environ.get('HYDRA_UMC_CI'), os.environ.get('HTTPS_PROXY'))\n")
    make_repo(tmp_path / "ws", "a", test=code)
    cfg = config(tmp_path, ["a"], full={"passEnv": ["KEEP_ME", "MY_API_TOKEN"], "includeCiValidate": False})
    report = run_plan(tmp_path, cfg)
    text = json.dumps(report)
    assert "hunter2" not in text and "sekret-value" not in text
    assert "['KEEP_ME']" in text and "visible-unrelated" not in text
    assert "ci 1 http://127.0.0.1:9" in text  # offline hints because the command does not need the network


def test_a_repository_that_needs_the_network_is_left_out_unless_allowed(tmp_path: Path) -> None:
    manifest = {"developer_node": {"full_test": {"interpreter": "python", "script": "tools/build_test.py", "needs_network": True}}}
    make_repo(tmp_path / "ws", "net", test="import os\nprint('proxy', os.environ.get('HTTPS_PROXY'))\n", manifest=manifest)
    off = run_plan(tmp_path, config(tmp_path, ["net"], full={"includeCiValidate": False}))
    assert off["results"][0]["status"] == "skipped" and "network" in off["results"][0]["note"]  # type: ignore[index]
    on = run_plan(tmp_path, config(tmp_path, ["net"], full={"includeCiValidate": False, "allowNetwork": True}))
    assert on["results"][0]["status"] == "pass" and "proxy None" in json.dumps(on)  # type: ignore[index]


def test_commands_run_one_at_a_time_and_a_failed_ci_skips_the_heavy_test(tmp_path: Path) -> None:
    log = (tmp_path / "log.txt").as_posix()
    body = f"import time\nopen(r'{log}','a').write('start\\n')\ntime.sleep(0.4)\nopen(r'{log}','a').write('end\\n')\n"
    ws = tmp_path / "ws"
    for name in ("a", "b", "c"):
        make_repo(ws, name, ci=body, test=body)
    make_repo(ws, "broken", ci="raise SystemExit(2)\n", test=f"open(r'{log}','a').write('SHOULD NOT RUN\\n')\n")
    cfg = config(tmp_path, ["a", "b", "c", "broken"])
    report = run_plan(tmp_path, cfg)
    lines = (tmp_path / "log.txt").read_text().split()
    assert lines == ["start", "end"] * 6  # never two at once
    broken = by_command(report, "broken")
    assert broken["ci"]["status"] == "fail" and broken["ci"]["exit_code"] == 2 and broken["full"]["status"] == "skipped"
    assert [item["repo"] for item in report["results"]] == ["a", "a", "b", "b", "c", "c", "broken", "broken"]  # type: ignore[attr-defined]


def test_cancelling_kills_only_the_child_and_skips_the_rest(tmp_path: Path) -> None:
    beat = (tmp_path / "beat.txt").as_posix()
    spin = f"import time\nwhile True:\n    open(r'{beat}','w').write(str(time.time()))\n    time.sleep(0.05)\n"
    ws = tmp_path / "ws"
    make_repo(ws, "long", test=spin)
    make_repo(ws, "after")
    cfg = config(tmp_path, ["long", "after"], full={"includeCiValidate": False})

    def cancel(_pid: int) -> None:
        time.sleep(0.6)
        raise KeyboardInterrupt

    report = run_plan(tmp_path, cfg, on_start=cancel)
    assert report["aborted"] == "cancelled" and plugin_full.exit_code(report) == 1  # type: ignore[arg-type]
    assert [item["status"] for item in report["results"]] == ["skipped", "skipped"]  # type: ignore[attr-defined]
    stamp = (tmp_path / "beat.txt").read_text()
    time.sleep(0.6)
    assert (tmp_path / "beat.txt").read_text() == stamp  # the child is dead: its heartbeat stopped
    assert json.loads((tmp_path / "data" / "ci-reports" / "full-latest.json").read_text())["aborted"] == "cancelled"


def test_too_little_free_disk_refuses_before_and_stops_during_the_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ws = tmp_path / "ws"
    marker = (tmp_path / "marker").as_posix()
    make_repo(ws, "a", test=f"open(r'{marker}','w').write('ran')\n")
    make_repo(ws, "b")
    cfg = config(tmp_path, ["a", "b"], full={"minFreeGb": 10})
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full)
    monkeypatch.setattr(plugin_full, "free_bytes", lambda _p: 9 * 1024**3)
    with Store(tmp_path / "s.db") as store:
        approve(store, plan)
        with pytest.raises(plugin_ci.PluginError, match="free"):
            plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW)
        assert not (tmp_path / "marker").exists()
        calls = {"n": 0}

        def shrinking(_p: Path) -> int:
            calls["n"] += 1
            return (50 if calls["n"] <= 3 else 1) * 1024**3  # enough for the first check and the first command, then not

        monkeypatch.setattr(plugin_full, "free_bytes", shrinking)
        report = plugin_full.run(plan, store, cfg.ecosystem_ci, cfg.ecosystem_ci_full, cfg.data_path(), (), NOW)  # the approval was not spent
    assert report["aborted"] == "low_disk" and plugin_full.exit_code(report) == 1
    statuses = [item["status"] for item in report["results"]]
    assert statuses[0] == "pass" and report["summary"]["skipped"] >= 1


def test_the_panel_shows_the_last_complete_report(tmp_path: Path) -> None:
    make_repo(tmp_path / "ws", "a")
    cfg = config(tmp_path, ["a"])
    run_plan(tmp_path, cfg)
    with Store(tmp_path / "s.db") as store:
        status = panel.build_status(settings(dataDir=str(cfg.data_path()), panel={"enabled": True}, language="pt"), store, NOW)
    assert status["health"]["last_ci_full_report"]["summary"]["pass"] == 2
    assert status["labels"]["status_timeout"] == "tempo esgotado" and "ci_full_report" in status["labels"]


def test_the_cli_plans_approves_with_a_terminal_and_exits_nonzero_on_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ws = tmp_path / "ws"
    make_repo(ws, "good")
    make_repo(ws, "bad", test="raise SystemExit(3)\n")
    cfg = config(tmp_path, ["good", "bad"])
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"dataDir": str(cfg.data_path()), "ecosystemCi": {"enabled": True, "workspace": str(ws), "repos": ["good", "bad"]},
                                "ecosystemCiFull": {"enabled": True, "minFreeGb": 0.001, "perRepoTimeoutSeconds": 20}}), encoding="utf-8")
    base = ["--config", str(path), "--lang", "es", "plugin"]
    assert cli.main([*base, "full-plan"]) == 0
    out = capsys.readouterr().out
    assert "good: " in out and "build_test.py" in out and "Revise los comandos" in out
    assert cli.main([*base, "full-approve"]) == 1  # no terminal: nothing approved
    assert "terminal" in capsys.readouterr().err
    assert cli.main([*base, "full-run"]) == 1  # no approval: nothing runs
    assert "approval" in capsys.readouterr().err
    plan = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full, ("bad",))
    with Store(cfg.data_path() / "node.sqlite") as store:
        approve(store, plan, time.time())
    assert cli.main([*base, "full-run", "--exclude", "bad"]) == 0
    assert "CI completo del ecosistema: 2 correctos" in capsys.readouterr().out
    full = plugin_full.build_plan(cfg.ecosystem_ci, cfg.ecosystem_ci_full)
    with Store(cfg.data_path() / "node.sqlite") as store:
        approve(store, full, time.time())
    assert cli.main([*base, "full-run"]) == 1
    assert "fallido" in capsys.readouterr().out
