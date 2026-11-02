import json
from pathlib import Path

import pytest
from hydra_umc_developer_node import __version__, cli
from support import SECRET, make_bundle, make_message, make_repo, write_json

import time


def config_file(tmp_path: Path, **sections: object) -> str:
    document: dict[str, object] = {"dataDir": str(tmp_path / "data")}
    document.update(sections)
    return str(write_json(tmp_path / "config.json", document))


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = cli.main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_version_and_usage(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        cli.main(["--version"])
    assert stop.value.code == 0
    assert __version__ in capsys.readouterr().out
    with pytest.raises(SystemExit) as stop:
        cli.main([])
    assert stop.value.code == 2


def test_config_check_lists_the_closed_switches(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, out, _ = run(capsys, "--config", config_file(tmp_path), "config", "check")
    assert code == 0 and "ingest" in out and "ecosystemCi" in out
    code, out, _ = run(capsys, "--config", config_file(tmp_path), "--lang", "es", "config", "check")
    assert "interruptores apagados" in out
    code, out, _ = run(capsys, "--config", config_file(tmp_path, panel={"enabled": True}), "config", "show")
    assert json.loads(out)["switches"]["panel"] is True


def test_a_bad_configuration_is_a_refusal_not_a_crash(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, _, err = run(capsys, "--config", config_file(tmp_path, ingest={"enabled": "yes"}), "config", "check")
    assert code == 1 and "Refused" in err


def test_verify_is_read_only_and_ingest_is_closed_by_default(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    bundle = write_json(tmp_path / "b.json", make_bundle())
    code, out, _ = run(capsys, "evidence", "verify", str(bundle))
    assert code == 0 and "2 reproduction steps" in out
    code, _, err = run(capsys, "--config", config_file(tmp_path), "evidence", "ingest", str(bundle))
    assert code == 1 and "closed" in err


def test_ingest_then_list_and_show(capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HYDRA_UMC_DEVELOPER_NODE_TRANSPORT_SECRET", SECRET)
    config = config_file(tmp_path, ingest={"enabled": True})
    message = write_json(tmp_path / "m.json", make_message(make_bundle(), time.time()))
    code, out, _ = run(capsys, "--config", config, "--lang", "pt", "evidence", "ingest", str(message))
    assert code == 0 and "guardado" in out
    code, out, _ = run(capsys, "--config", config, "case", "list")
    assert "esc-1\tawaiting-review\ttransport" in out
    code, out, _ = run(capsys, "--config", config, "case", "show", "esc-1")
    assert json.loads(out)["bundle"]["impact"] == "the server does not answer"
    code, _, err = run(capsys, "--config", config, "case", "show", "nope")
    assert code == 1 and "unknown case" in err


def test_empty_list_in_another_language(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, out, _ = run(capsys, "--config", config_file(tmp_path, language="ja"), "case", "list")
    assert code == 0 and "ケースはありません" in out


def test_approving_needs_a_terminal(capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HYDRA_UMC_DEVELOPER_NODE_TRANSPORT_SECRET", SECRET)
    config = config_file(tmp_path, ingest={"enabled": True}, repro={"enabled": True, "allowedCommands": ["python"]})
    run(capsys, "--config", config, "evidence", "ingest", str(write_json(tmp_path / "m.json", make_message(make_bundle(), time.time()))))
    recipe = write_json(tmp_path / "r.json", {"schema_version": "1.0", "scenario_id": "s", "repro_case": "c",
                                              "steps": [{"argv": ["python", "-c", "pass"]}], "reproduced_when": {"exit_code_not": 0}})
    code, out, _ = run(capsys, "--config", config, "repro", "check", str(recipe))
    assert code == 0 and len(out.strip()) == 64
    code, _, err = run(capsys, "--config", config, "repro", "approve", "esc-1", str(recipe))
    assert code == 1 and "terminal" in err
    code, _, err = run(capsys, "--config", config, "repro", "run", "esc-1", str(recipe), "--phase", "before", "--workdir", str(tmp_path),
                       "--fingerprint", "abc")
    assert code == 1 and "approval" in err


def test_checkout_commands_use_the_cache(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    remote = tmp_path / "remotes" / "app"
    sha = make_repo(remote)
    config = config_file(tmp_path, checkouts={"enabled": True, "allowedRemotes": [str(remote.parent)]})
    code, out, _ = run(capsys, "--config", config, "checkout", "fetch", "app", str(remote), "HEAD")
    assert code == 0 and sha in out
    code, out, _ = run(capsys, "--config", config, "checkout", "list")
    assert json.loads(out)["entries"][0]["sha"] == sha
    code, out, _ = run(capsys, "--config", config, "checkout", "prune")
    assert code == 0 and "0 worktree" in out
    code, _, err = run(capsys, "--config", config_file(tmp_path), "checkout", "fetch", "app", str(remote), "HEAD")
    assert code == 1 and "closed" in err


def test_panel_and_plugin_commands(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    code, _, err = run(capsys, "--config", config_file(tmp_path), "panel", "status")
    assert code == 1 and "closed" in err
    config = config_file(tmp_path, panel={"enabled": True}, ecosystemCi={"workspace": str(tmp_path), "repos": ["x"]})
    code, out, _ = run(capsys, "--config", config, "panel", "status")
    assert code == 0 and json.loads(out)["contract"] == "developer-node-status/1"
    code, out, _ = run(capsys, "--config", config, "panel", "export")
    assert Path(out.strip()).name == "status.json"
    code, out, _ = run(capsys, "--config", config, "plugin", "list")
    assert json.loads(out) == [{"name": "ecosystem-ci", "enabled": False}]
    code, out, _ = run(capsys, "--config", config, "plugin", "plan")
    assert len(json.loads(out)["sha256"]) == 64
    code, _, err = run(capsys, "--config", config, "plugin", "run")
    assert code == 1 and "closed" in err
    code, _, err = run(capsys, "--config", config, "plugin", "approve")
    assert code == 1 and "terminal" in err
