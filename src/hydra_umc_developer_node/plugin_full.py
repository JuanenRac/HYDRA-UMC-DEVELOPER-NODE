# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/plugin_full.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The complete mode of the `ecosystem-ci` plugin: the shared CI validator and the heavy tests a repository declares.

A repository declares its heavy test in its manifest (`developer_node.full_test`: an interpreter, a script inside the repository and
whether it needs the network). A repository that declares nothing runs nothing. The plan lists, repository by repository, the exact
command that would start, with the SHA-256 of each script, and a person approves the whole batch by its digest (it expires and is used
up by the run). The run is serial, never parallel, bounded in time per repository and in total, bounded in output, started with a
minimal environment, and it never starts anything that is not in the approved plan. If free disk space falls under the limit it stops.

The network is not sandboxed: a repository that does not declare that it needs the network gets an environment that tells the common
tools to stay offline (empty proxy, offline flags), and a repository that needs it is left out unless the configuration allows it.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import approvals
from .plugin_ci import PluginError
from .redaction import redact
from .schema import validate
from .settings import EcosystemCiFullSettings, EcosystemCiSettings
from .store import Store

NAME = "ecosystem-ci-full"
ACTION = "ci-full-run"
SUBJECT = "plan:ecosystem-ci-full"
INTERPRETERS = ("python", "sh")
STATUSES = ("pass", "fail", "timeout", "skipped")
MAX_LINE = 300
_SECRET_WORDS = ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "API_KEY", "APIKEY", "PRIVATE", "CREDENTIAL")
_BASE_ENV = ("PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME", "HOMEDRIVE", "HOMEPATH",
             "USERPROFILE", "APPDATA", "LOCALAPPDATA", "LANG", "LC_ALL", "TZ", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS")
_OFFLINE_ENV = {
    "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9", "ALL_PROXY": "http://127.0.0.1:9", "NO_PROXY": "",
    "PIP_NO_INDEX": "1", "npm_config_offline": "true", "CARGO_NET_OFFLINE": "true", "GRADLE_OPTS": "--offline",
}


def free_bytes(path: Path) -> int:
    """Free space of the disk that holds `path` (a function of its own so a test can set it)."""
    return shutil.disk_usage(path).free


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plain_name(name: str) -> bool:
    return bool(name) and name not in (".", "..") and "/" not in name and "\\" not in name


def _declared(folder: Path, manifest_file: str) -> tuple[dict[str, Any] | None, str]:
    """The `developer_node.full_test` of a manifest, or (None, reason)."""
    try:
        manifest = json.loads((folder / manifest_file).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "no readable manifest"
    node = manifest.get("developer_node") if isinstance(manifest, dict) else None
    declared = node.get("full_test") if isinstance(node, dict) else None
    if declared is None:
        return None, "no heavy test declared"
    if not isinstance(declared, dict):
        return None, "the declaration is not an object"
    script = declared.get("script")
    if declared.get("interpreter") not in INTERPRETERS or not isinstance(script, str) or not script:
        return None, "the declaration needs an interpreter (python or sh) and a script"
    parts = Path(script)
    if parts.is_absolute() or ".." in parts.parts or "\\" in script:
        return None, "the script must be a relative path inside the repository"
    if not isinstance(declared.get("needs_network", False), bool):
        return None, "needs_network must be true or false"
    return declared, ""


def _command(identifier: str, interpreter: str, script: str, needs_network: bool, folder: Path) -> dict[str, Any]:
    argv = ["python", "-I", script] if identifier == "ci_validate" else [interpreter, script]
    return {"id": identifier, "argv": argv, "script_sha256": _sha256(folder / script), "needs_network": needs_network}


def build_plan(ci: EcosystemCiSettings, full: EcosystemCiFullSettings, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    """The plan: for each repository, the exact commands (or the reason it runs nothing). `exclude` removes repositories before approval."""
    if not ci.workspace:
        raise PluginError("ecosystemCi.workspace is not set in the configuration file")
    if not ci.repos:
        raise PluginError("ecosystemCi.repos lists no repository")
    if not _plain_name(full.manifest_file):
        raise PluginError("ecosystemCiFull.manifestFile must be a plain file name")
    unknown = [name for name in exclude if name not in ci.repos]
    if unknown:
        raise PluginError(f"cannot exclude {unknown[0]!r}: it is not in ecosystemCi.repos")
    workspace = Path(ci.workspace).expanduser()
    repos: list[dict[str, Any]] = []
    for name in ci.repos:
        if not _plain_name(name):
            raise PluginError(f"{name!r} is not a plain repository folder name")
        if name in exclude:
            continue
        folder = workspace / name
        commands: list[dict[str, Any]] = []
        notes: list[str] = []
        if full.include_ci_validate:
            if (folder / "tools" / "ci_validate.py").is_file():
                commands.append(_command("ci_validate", "python", "tools/ci_validate.py", False, folder))
            else:
                notes.append("tools/ci_validate.py not found")
        declared, reason = _declared(folder, full.manifest_file)
        if declared is not None:
            script = declared["script"]
            if (folder / script).is_file():
                commands.append(_command("full_test", declared["interpreter"], script, bool(declared.get("needs_network", False)), folder))
            else:
                notes.append(f"the declared script {script} was not found")
        else:
            notes.append(reason)
        repos.append({"repo": name, "commands": commands, "note": "; ".join(notes) if not commands else ""})
    if not repos:
        raise PluginError("every repository was excluded: nothing to run")
    return {
        "contract": "ecosystem-ci-full-plan/1",
        "workspace": str(workspace),
        "limits": {"per_repo_timeout_seconds": full.per_repo_timeout_seconds, "total_timeout_seconds": full.total_timeout_seconds,
                   "max_output_bytes": full.max_output_bytes, "min_free_gb": full.min_free_gb, "allow_network": full.allow_network},
        "pass_env": sorted(full.pass_env),
        "excluded": sorted(exclude),
        "repos": repos,
    }


def plan_digest(plan: dict[str, Any]) -> str:
    return approvals.digest_of(plan)


def describe(plan: dict[str, Any]) -> list[str]:
    """One line per command (or per repository that runs nothing), for the person who is about to approve."""
    lines: list[str] = []
    for item in plan["repos"]:
        if not item["commands"]:
            lines.append(f"{item['repo']}: nothing will run ({item['note']})")
        for command in item["commands"]:
            net = " [network]" if command["needs_network"] else ""
            lines.append(f"{item['repo']}: {' '.join(command['argv'])}{net}")
    return lines


def environment(extra: tuple[str, ...], offline: bool) -> dict[str, str]:
    """A minimal environment: a short list of names, plus the configured ones, never a name that looks like a secret."""
    wanted = {name.upper() for name in (*_BASE_ENV, *extra)}
    kept = {key: value for key, value in os.environ.items() if key.upper() in wanted and not any(word in key.upper() for word in _SECRET_WORDS)}
    kept["HYDRA_UMC_CI"] = "1"
    kept["PYTHONIOENCODING"] = "utf-8"
    if offline:
        kept.update(_OFFLINE_ENV)
    return kept


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Ends the child this module started and the processes it started; nothing else."""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False, timeout=30)
        else:
            import signal

            os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError, subprocess.SubprocessError):
        pass
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.SubprocessError:
        pass


def _argv(command: dict[str, Any]) -> list[str]:
    program = command["argv"][0]
    if program == "python":
        return [sys.executable, *command["argv"][1:]]
    found = shutil.which(program)
    return [found or program, *command["argv"][1:]]


def _execute(command: dict[str, Any], folder: Path, env: dict[str, str], seconds: float, full: EcosystemCiFullSettings,
             on_start: Callable[[int], None] | None) -> dict[str, Any]:
    started = time.monotonic()
    extra: dict[str, Any] = {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if sys.platform == "win32" else {"start_new_session": True}
    try:
        process = subprocess.Popen(_argv(command), cwd=str(folder), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, **extra)
    except OSError as error:
        return {"status": "fail", "exit_code": None, "seconds": 0.0, "lines": [], "note": f"could not start: {error.__class__.__name__}"}
    chunks: list[bytes] = []
    state = {"total": 0, "over": False}

    def read() -> None:
        assert process.stdout is not None
        while True:
            block = process.stdout.read(8192)
            if not block:
                return
            state["total"] += len(block)
            if state["total"] > full.max_output_bytes:
                state["over"] = True
                return
            chunks.append(block)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    status, note = "", ""
    try:
        if on_start is not None:
            on_start(process.pid)
        deadline = started + seconds
        while process.poll() is None:
            if state["over"]:
                status, note = "fail", "output limit reached: the command was stopped"
                break
            if time.monotonic() >= deadline:
                status, note = "timeout", "time limit reached: the command was stopped"
                break
            time.sleep(0.05)
        if status:
            _kill_tree(process)
        else:
            reader.join(timeout=5)
            if state["over"]:
                status, note = "fail", "output limit reached"
    except BaseException:
        _kill_tree(process)
        raise
    finally:
        reader.join(timeout=2)
        if process.stdout is not None:
            process.stdout.close()
    code = process.returncode
    if not status:
        status = "pass" if code == 0 else "fail"
    text = b"".join(chunks).decode("utf-8", errors="replace")
    lines = [redact(line)[:MAX_LINE] for line in text.splitlines() if line.strip()]
    return {"status": status, "exit_code": code if status in ("pass", "fail") and not note else None, "seconds": round(time.monotonic() - started, 2),
            "lines": lines[-full.tail_lines:], "note": note}


def _result(repo: str, command: str, status: str, note: str = "", **more: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"repo": repo, "command": command, "status": status, "exit_code": None, "seconds": 0.0, "tail": [], "note": note}
    base.update(more)
    return base


def run(plan: dict[str, Any], store: Store, ci: EcosystemCiSettings, full: EcosystemCiFullSettings, data_dir: Path,
        exclude: tuple[str, ...] = (), now: float | None = None, on_start: Callable[[int], None] | None = None) -> dict[str, Any]:
    """Runs the approved plan, serially, and writes the consolidated report. Nothing outside the plan is ever started."""
    if not ci.enabled:
        raise PluginError("ecosystemCi is closed: set ecosystemCi.enabled to true in the configuration file")
    if not full.enabled:
        raise PluginError("ecosystemCiFull is closed: set ecosystemCiFull.enabled to true in the configuration file")
    if plan != build_plan(ci, full, exclude):
        raise PluginError("the plan is not the one the configuration describes (a repository, a script or a limit changed)")
    workspace = Path(plan["workspace"])
    if free_bytes(workspace) < full.min_free_bytes:
        raise PluginError(f"less than {full.min_free_gb:g} GB free on the disk of the workspace: nothing was run")
    digest = plan_digest(plan)
    try:
        approvals.require(store, SUBJECT, ACTION, digest, full.approval_max_age_minutes, now)
    except approvals.ApprovalError as error:
        raise PluginError(str(error)) from error
    started = time.time() if now is None else now
    began = time.monotonic()
    results: list[dict[str, Any]] = []
    aborted: str | None = None
    try:
        for item in plan["repos"]:
            repo = item["repo"]
            if not item["commands"]:
                results.append(_result(repo, "", "skipped", item["note"]))
                continue
            previous_failed = False
            for command in item["commands"]:
                label = " ".join(command["argv"])
                if aborted:
                    results.append(_result(repo, label, "skipped", f"stopped before this command ({aborted})"))
                    continue
                if previous_failed:
                    results.append(_result(repo, label, "skipped", "the previous command of this repository did not pass"))
                    continue
                if command["needs_network"] and not full.allow_network:
                    results.append(_result(repo, label, "skipped", "needs the network and ecosystemCiFull.allowNetwork is false"))
                    continue
                remaining = full.total_timeout_seconds - (time.monotonic() - began)
                if remaining <= 0:
                    aborted = "total_timeout"
                    results.append(_result(repo, label, "skipped", "stopped before this command (total_timeout)"))
                    continue
                if free_bytes(workspace) < full.min_free_bytes:
                    aborted = "low_disk"
                    results.append(_result(repo, label, "skipped", "stopped before this command (low_disk)"))
                    continue
                folder = workspace / repo
                script = folder / command["argv"][-1]
                if not script.is_file() or _sha256(script) != command["script_sha256"]:
                    results.append(_result(repo, label, "skipped", "the script changed after the plan was made"))
                    previous_failed = True
                    continue
                env = environment(full.pass_env, offline=not (command["needs_network"] and full.allow_network))
                try:
                    outcome = _execute(command, folder, env, min(full.per_repo_timeout_seconds, remaining), full, on_start)
                except KeyboardInterrupt:
                    aborted = "cancelled"
                    results.append(_result(repo, label, "skipped", "cancelled by the person"))
                    continue
                results.append(_result(repo, label, outcome["status"], outcome["note"], exit_code=outcome["exit_code"], seconds=outcome["seconds"],
                                       tail=outcome["lines"]))
                previous_failed = outcome["status"] != "pass"
    except KeyboardInterrupt:
        aborted = "cancelled"
    done = {(item["repo"], item["command"]) for item in results}
    for item in plan["repos"]:
        if not item["commands"] and (item["repo"], "") not in done:
            results.append(_result(item["repo"], "", "skipped", item["note"]))
        for command in item["commands"]:
            label = " ".join(command["argv"])
            if (item["repo"], label) not in done:
                results.append(_result(item["repo"], label, "skipped", f"stopped before this command ({aborted})"))
    summary = {key: sum(1 for item in results if item["status"] == key) for key in STATUSES}
    report = {"contract": "ecosystem-ci-full-report/1", "plan_digest": digest, "started_at": started, "finished_at": time.time(),
              "aborted": aborted, "results": results, "summary": summary}
    validate("ecosystem_ci_full_report", report)
    folder = data_dir / "ci-reports"
    folder.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    (folder / f"full-report-{int(started)}.json").write_text(text, encoding="utf-8")
    temporary = folder / "full-latest.json.tmp"
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, folder / "full-latest.json")
    store.log("ci-full-run", f"{summary['pass']} pass, {summary['fail']} fail, {summary['timeout']} timeout, {summary['skipped']} skipped"
              + (f", aborted: {aborted}" if aborted else ""), None, now)
    return report


def exit_code(report: dict[str, Any]) -> int:
    """0 only when nothing failed, nothing timed out and the run was not cut short."""
    summary = report["summary"]
    return 0 if summary["fail"] == 0 and summary["timeout"] == 0 and not report["aborted"] else 1


def latest_report(data_dir: Path) -> dict[str, Any] | None:
    try:
        loaded = json.loads((data_dir / "ci-reports" / "full-latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None

