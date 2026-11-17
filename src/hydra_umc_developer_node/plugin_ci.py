# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/plugin_ci.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The `ecosystem-ci` plugin: the shared CI validator of every repository of a workspace, one report.

Every repository of the family carries the same `tools/ci_validate.py`. This plugin runs it, one repository after another, with
`HYDRA_UMC_CI=1` (so nothing changes a version), and writes one consolidated report. Because that runs code of the repositories, it is
closed by default and it needs a person to approve the exact plan (the workspace, the list of repositories and the command) first. The
report stays on this machine; nothing is sent anywhere.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from . import approvals
from .procs import run_bounded
from .redaction import redact
from .schema import validate
from .settings import EcosystemCiSettings
from .store import Store

NAME = "ecosystem-ci"
ACTION = "ci-run"
SUBJECT = "plan:ecosystem-ci"
MAX_OUTPUT_BYTES = 4_000_000
_SECRET_WORDS = ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "API_KEY", "APIKEY", "PRIVATE")


class PluginError(ValueError):
    """The plugin is closed, the plan is wrong or no approval exists; nothing was run when this is raised."""


def _environment() -> dict[str, str]:
    kept = {key: value for key, value in os.environ.items() if not any(word in key.upper() for word in _SECRET_WORDS)}
    kept["HYDRA_UMC_CI"] = "1"
    return kept


def _script_sha256(path: Path) -> str:
    """The SHA-256 of the validator a repository would run (empty when there is none), so that a script changed after the approval is not run."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def build_plan(settings: EcosystemCiSettings) -> dict[str, Any]:
    if not settings.workspace:
        raise PluginError("ecosystemCi.workspace is not set in the configuration file")
    if not settings.repos:
        raise PluginError("ecosystemCi.repos lists no repository")
    workspace = Path(settings.workspace).expanduser()
    repos = []
    for name in settings.repos:
        if name in (".", "..") or "/" in name or "\\" in name:
            raise PluginError(f"{name!r} is not a plain repository folder name")
        repos.append(name)
    scripts = {name: _script_sha256(workspace / name / "tools" / "ci_validate.py") for name in repos}
    return {
        "contract": "ecosystem-ci-plan/1",
        "workspace": str(workspace),
        "repos": repos,
        "command": ["python", "-I", "tools/ci_validate.py"],
        "env": {"HYDRA_UMC_CI": "1"},
        "scripts": scripts,
        "timeout_seconds": settings.timeout_seconds,
    }


def plan_digest(plan: dict[str, Any]) -> str:
    return approvals.digest_of(plan)


def _run_repo(workspace: Path, name: str, settings: EcosystemCiSettings, approved_sha256: str = "") -> dict[str, Any]:
    folder = workspace / name
    script = folder / "tools" / "ci_validate.py"
    if not script.is_file():
        return {"repo": name, "status": "skipped", "exit_code": None, "seconds": 0.0, "tail": ["tools/ci_validate.py not found"]}
    if approved_sha256 and _script_sha256(script) != approved_sha256:
        return {"repo": name, "status": "error", "exit_code": None, "seconds": 0.0,
                "tail": ["tools/ci_validate.py changed after the plan was approved: it was not run"]}
    try:
        result = run_bounded([sys.executable, "-I", "tools/ci_validate.py"], folder, _environment(), settings.timeout_seconds, MAX_OUTPUT_BYTES)
    except OSError as error:
        return {"repo": name, "status": "error", "exit_code": None, "seconds": 0.0, "tail": [f"could not start: {error.__class__.__name__}"]}
    lines = [redact(line) for line in result.output.decode("utf-8", "replace").splitlines() if line.strip()]
    if result.status == "timeout":
        return {"repo": name, "status": "error", "exit_code": None, "seconds": result.seconds, "tail": ["timeout"]}
    if result.status == "over":
        return {"repo": name, "status": "error", "exit_code": None, "seconds": result.seconds,
                "tail": ["output limit reached: the command was stopped", *lines[-settings.tail_lines:]]}
    return {"repo": name, "status": "pass" if result.returncode == 0 else "fail", "exit_code": result.returncode,
            "seconds": result.seconds, "tail": lines[-settings.tail_lines:]}


def run(plan: dict[str, Any], store: Store, settings: EcosystemCiSettings, data_dir: Path, now: float | None = None) -> dict[str, Any]:
    """Runs an approved plan, one repository at a time, and writes the consolidated report. Returns the report."""
    if not settings.enabled:
        raise PluginError("ecosystemCi is closed: set ecosystemCi.enabled to true in the configuration file")
    if plan != build_plan(settings):
        raise PluginError("the plan is not the one the configuration describes")
    digest = plan_digest(plan)
    try:
        approvals.require(store, SUBJECT, ACTION, digest, settings.approval_max_age_minutes, now)
    except approvals.ApprovalError as error:
        raise PluginError(str(error)) from error
    workspace = Path(plan["workspace"])
    started = time.time() if now is None else now
    results = [_run_repo(workspace, name, settings, plan.get("scripts", {}).get(name, "")) for name in plan["repos"]]
    summary = {key: sum(1 for item in results if item["status"] == key) for key in ("pass", "fail", "error", "skipped")}
    report = {"contract": "ecosystem-ci-report/1", "plan_digest": digest, "started_at": started, "finished_at": time.time(),
              "results": results, "summary": summary}
    validate("ecosystem_ci_report", report)
    folder = data_dir / "ci-reports"
    folder.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True)
    (folder / f"report-{int(started)}.json").write_text(text, encoding="utf-8")
    temporary = folder / "latest.json.tmp"
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, folder / "latest.json")
    store.log("ci-run", f"{summary['pass']} pass, {summary['fail']} fail, {summary['error']} error, {summary['skipped']} skipped", None, now)
    return report


def latest_report(data_dir: Path) -> dict[str, Any] | None:
    path = data_dir / "ci-reports" / "latest.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None
