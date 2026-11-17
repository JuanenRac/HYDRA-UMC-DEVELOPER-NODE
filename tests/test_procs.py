"""The bounded runner shared by the reproduction steps and the CI plugin: time, output, the tree of processes, and the script digest of the plan."""
import sys
import textwrap
import time
from pathlib import Path

import pytest
from hydra_umc_developer_node import plugin_ci, procs
from hydra_umc_developer_node.settings import EcosystemCiSettings


def test_a_command_that_ends_gives_its_output_and_code(tmp_path: Path) -> None:
    result = procs.run_bounded([sys.executable, "-c", "print('hello'); raise SystemExit(3)"], tmp_path, {}, 20, 1000)
    assert (result.status, result.returncode) == ("ok", 3)
    assert b"hello" in result.output


def test_output_over_the_limit_stops_the_command(tmp_path: Path) -> None:
    code = "import sys\nwhile True:\n    sys.stdout.write('x' * 4096)\n    sys.stdout.flush()\n"
    result = procs.run_bounded([sys.executable, "-c", code], tmp_path, {}, 30, 20_000)
    assert result.status == "over"
    assert len(result.output) <= 20_000


def test_a_step_that_starts_a_sleeping_child_is_ended_with_it(tmp_path: Path) -> None:
    marker = tmp_path / "child-alive"
    child = textwrap.dedent(
        f"""
        import pathlib, time
        for _ in range(200):
            pathlib.Path({str(marker)!r}).write_text(str(time.time()))
            time.sleep(0.05)
        """
    )
    parent = f"import subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', {child!r}])\ntime.sleep(60)\n"
    result = procs.run_bounded([sys.executable, "-c", parent], tmp_path, {}, 1.5, 1000)
    assert result.status == "timeout"
    time.sleep(0.5)
    first = marker.read_text() if marker.exists() else ""
    time.sleep(0.6)
    assert (marker.read_text() if marker.exists() else "") == first, "the child kept running after the tree was ended"


def test_a_program_that_cannot_start_raises_oserror(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        procs.run_bounded([str(tmp_path / "no-such-program")], tmp_path, {}, 5, 100)


def test_the_plan_carries_the_digest_of_each_validator_and_a_changed_script_is_not_run(tmp_path: Path) -> None:
    repo = tmp_path / "REPO"
    (repo / "tools").mkdir(parents=True)
    script = repo / "tools" / "ci_validate.py"
    script.write_text("print('ok')\n", encoding="utf-8")
    settings = EcosystemCiSettings(enabled=True, workspace=str(tmp_path), repos=("REPO",))
    plan = plugin_ci.build_plan(settings)
    assert len(plan["scripts"]["REPO"]) == 64
    assert plugin_ci._run_repo(tmp_path, "REPO", settings, plan["scripts"]["REPO"])["status"] == "pass"
    script.write_text("print('changed')\n", encoding="utf-8")
    refused = plugin_ci._run_repo(tmp_path, "REPO", settings, plan["scripts"]["REPO"])
    assert refused["status"] == "error" and "changed after the plan was approved" in refused["tail"][0]
    assert plugin_ci.build_plan(settings)["scripts"]["REPO"] != plan["scripts"]["REPO"]
