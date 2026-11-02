"""Helpers shared by the tests: a valid bundle, a signed message, a tiny git repository and a settings builder."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from hydra_umc_developer_node.evidence import bundle_checksum, sign_message
from hydra_umc_developer_node.settings import Settings, parse_settings

SECRET = "x" * 32


def make_bundle(**overrides: Any) -> dict[str, Any]:
    bundle: dict[str, Any] = {
        "componentVersions": {"HYDRA-UMC-SERVER": "0.8.0.7"},
        "relevantManifests": ["HYDRA-UMC-SERVER: {}"],
        "redactedLogExcerpts": ["service stopped"],
        "reproductionSteps": ["systemctl is-active hydra-umc-server", "curl -s http://127.0.0.1:3000/health"],
        "failedTests": [],
        "impact": "the server does not answer",
        "actionsAttempted": [],
        "localValidationResult": "no local validation was run",
        "date": "1970-01-01T00:00:00Z",
    }
    bundle.update(overrides)
    bundle["checksum"] = bundle_checksum(bundle)
    return bundle


def make_message(bundle: dict[str, Any], now: float, nonce: str = "n-1", escalation_id: str = "esc-1", to_node: str = "developer-node") -> dict[str, Any]:
    body: dict[str, Any] = {
        "message_id": f"technician-{escalation_id}", "from_node": "technician", "to_node": to_node, "kind": "incident",
        "contract_version": "incident-transport/1", "nonce": nonce, "sent_at": now,
        "payload": {"escalationId": escalation_id, "evidenceBundle": bundle},
    }
    body["mac"] = sign_message(body, SECRET)
    return body


def settings(**sections: Any) -> Settings:
    return parse_settings(sections)


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", *args],
                            cwd=str(cwd), capture_output=True, text=True, check=True)
    return result.stdout.strip()


def make_repo(path: Path, files: dict[str, str] | None = None) -> str:
    """A small git repository with one commit; returns the commit hash."""
    path.mkdir(parents=True)
    git("init", "-q", cwd=path)
    for name, text in (files or {"a.txt": "one\n"}).items():
        (path / name).write_text(text, encoding="utf-8")
    git("add", "-A", cwd=path)
    git("commit", "-q", "-m", "first", cwd=path)
    return git("rev-parse", "HEAD", cwd=path)


def write_json(path: Path, document: Any) -> Path:
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


PY = Path(sys.executable).name
