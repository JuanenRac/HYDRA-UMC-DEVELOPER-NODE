# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/repro.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""An executable repro case: a recipe of fixed commands that shows a failure on one exact revision.

A recipe is a ReproRecipe document. It runs only when the `repro` switch is on, every command is in `repro.allowedCommands`, and a person
approved the exact digest of the recipe for that case; the approval is used up by the run. Commands are argument lists started without a
shell, in a folder inside the checkout, with a minimal environment, a time limit and a bound on the output, which is redacted before it
is kept. Each run yields a ScenarioOutcome (the shared contract of the SDK); the verdict of a before/after pair is computed by the SDK's
`compare_runs`, not by code of this repository: this module only refuses to guess when the SDK is not installed.
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import Any

from . import approvals
from .redaction import redact
from .schema import SchemaError, validate
from .settings import ReproSettings
from .store import Store

ACTION = "repro-run"


class ReproError(ValueError):
    """The recipe or the run is refused; nothing was started when this is raised before the run."""


def load_recipe(path: Path, settings: ReproSettings) -> dict[str, Any]:
    try:
        recipe = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ReproError(f"cannot read the recipe: {error.strerror or 'error'}") from error
    except ValueError as error:
        raise ReproError("the recipe is not valid JSON") from error
    return check_recipe(recipe, settings)


def check_recipe(recipe: Any, settings: ReproSettings) -> dict[str, Any]:
    try:
        validate("repro_recipe", recipe)
    except SchemaError as error:
        raise ReproError(f"the recipe is not a valid ReproRecipe: {error}") from error
    if len(recipe["steps"]) > settings.max_steps:
        raise ReproError("the recipe has more steps than repro.maxSteps")
    for step in recipe["steps"]:
        if not command_allowed(step["argv"][0], settings):
            raise ReproError(f"the command {PurePath(step['argv'][0]).name!r} is not in repro.allowedCommands")
        if "cwd" in step and _unsafe_folder(step["cwd"]):
            raise ReproError("the folder of a step must be relative and stay inside the checkout")
    return recipe  # type: ignore[no-any-return]


def _unsafe_folder(folder: str) -> bool:
    """True for a folder that is absolute (on any system), has a drive or a root, or climbs out with `..`."""
    for flavour in (PurePosixPath(folder), PureWindowsPath(folder)):
        if flavour.is_absolute() or flavour.drive or flavour.root or ".." in flavour.parts:
            return True
    return False


def command_name(command: str) -> str:
    name = command.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


def command_allowed(command: str, settings: ReproSettings) -> bool:
    return command_name(command) in {command_name(item) for item in settings.allowed_commands}


def _environment() -> dict[str, str]:
    kept = {key: value for key, value in os.environ.items() if key in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "USERPROFILE")}
    kept["HYDRA_UMC_DEVELOPER_NODE_REPRO"] = "1"
    return kept


def _inside(root: Path, candidate: Path) -> bool:
    root = root.resolve()
    candidate = candidate.resolve()
    return candidate == root or root in candidate.parents


def _run_step(argv: list[str], cwd: Path, settings: ReproSettings) -> tuple[str, int | None, str]:
    """('ok'|'timeout'|'error', exit code, redacted output tail)."""
    try:
        result = subprocess.run(argv, cwd=str(cwd), shell=False, env=_environment(), stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=settings.step_timeout_seconds, check=False)
    except subprocess.TimeoutExpired as error:
        partial = (error.stdout or b"") if isinstance(error.stdout, bytes) else b""
        return "timeout", None, redact(partial[-settings.max_output_bytes:].decode("utf-8", "replace"))
    except OSError as error:
        return "error", None, f"could not start: {error.__class__.__name__}"
    output = (result.stdout + result.stderr)[-settings.max_output_bytes:].decode("utf-8", "replace")
    return "ok", result.returncode, redact(output)


def run_recipe(recipe: dict[str, Any], store: Store, settings: ReproSettings, case_id: str, phase: str, workdir: Path,
               base_fingerprint: str, now: float | None = None) -> dict[str, Any]:
    """Runs an approved recipe in `workdir` and returns (and stores) its ScenarioOutcome."""
    if not settings.enabled:
        raise ReproError("repro is closed: set repro.enabled to true in the configuration file")
    if phase not in ("before", "after"):
        raise ReproError("the phase must be before or after")
    if not base_fingerprint:
        raise ReproError("the run needs the fingerprint of the exact source state (the commit)")
    check_recipe(recipe, settings)
    if not workdir.is_dir():
        raise ReproError("the work folder does not exist")
    store.get_case(case_id)
    try:
        approvals.require(store, case_id, ACTION, approvals.digest_of(recipe), settings.approval_max_age_minutes, now)
    except approvals.ApprovalError as error:
        raise ReproError(str(error)) from error

    outcome, exit_code, evidence = "error", None, ""
    steps = recipe["steps"]
    for index, step in enumerate(steps):
        cwd = workdir / step["cwd"] if "cwd" in step else workdir
        if not _inside(workdir, cwd) or not cwd.is_dir():
            evidence = "the folder of a step is not inside the checkout"
            break
        status, code, evidence = _run_step(step["argv"], cwd, settings)
        exit_code = code
        if status != "ok":
            outcome = "error"
            break
        if index < len(steps) - 1:
            if code != 0:
                outcome = "error"
                evidence = f"preparation step {index + 1} failed with exit code {code}: " + evidence
                break
            continue
        outcome = "reproduced" if code != recipe["reproduced_when"]["exit_code_not"] else "not-reproduced"
    document: dict[str, Any] = {
        "schema_version": "1.0",
        "scenario_id": recipe["scenario_id"],
        "run_id": "run-" + secrets.token_hex(6),
        "base_fingerprint": base_fingerprint,
        "phase": phase,
        "repro_case": recipe["repro_case"],
        "observed": {"outcome": outcome, "evidence": evidence},
        "timestamp_utc": datetime.fromtimestamp(time.time() if now is None else now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if exit_code is not None:
        document["observed"]["exit_code"] = exit_code
    validate("scenario-outcome", document)
    store.add_outcome(case_id, document)
    store.log("repro-run", f"{phase} {recipe['scenario_id']} -> {outcome}", case_id, now)
    return document


def compare(store: Store, case_id: str, scenario_id: str) -> dict[str, Any]:
    """The verdict of the stored before and after runs of a scenario, computed by the SDK."""
    before = store.latest_outcome(case_id, scenario_id, "before")
    after = store.latest_outcome(case_id, scenario_id, "after")
    if before is None or after is None:
        raise ReproError("both a before run and an after run are needed")
    try:
        from hydra_umc_sdk.scenario import compare_runs
    except ImportError as error:
        raise ReproError("the verdict is computed by the SDK: install this package with the sdk extra") from error
    verdict = compare_runs(before, after).to_dict()
    store.log("repro-compare", f"{scenario_id} -> {verdict['verdict']}", case_id)
    return verdict  # type: ignore[no-any-return]
