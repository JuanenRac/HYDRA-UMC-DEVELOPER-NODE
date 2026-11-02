# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/approvals.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Approval by a person: nothing that runs a command starts without one.

An approval is bound to one subject (a case or a plan), one action and the SHA-256 digest of the exact thing to be run, so a recipe that
was changed after approval needs a new approval. It expires after the time the configuration sets and is used up by the first run that
consumes it. Creating one needs a person at a terminal who types the first characters of the digest they have just been shown: input
that is not a terminal, an empty answer or a wrong one creates nothing.
"""
from __future__ import annotations

import getpass
import hashlib
import json
import sys
from collections.abc import Callable
from typing import Any, TextIO

from .store import Store

CONFIRM_LENGTH = 8


class ApprovalError(ValueError):
    """No approval was made or none is valid."""


def digest_of(document: Any) -> str:
    """SHA-256 of the canonical JSON of a recipe or a plan."""
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def current_person() -> str:
    try:
        return getpass.getuser()
    except Exception:  # no user name available on this host
        return "unknown"


def approve(store: Store, subject: str, action: str, digest: str, prompt: Callable[[str], str] | None = None,
            stream: TextIO | None = None, approver: str | None = None, now: float | None = None) -> None:
    """Records an approval after the person confirmed it. `prompt` is injected by tests; the real one needs a terminal."""
    stream = stream or sys.stdin
    if prompt is None:
        if not stream.isatty():
            raise ApprovalError("an approval needs a person at a terminal: nothing was approved")
        prompt = input
    typed = prompt(f"{action} {subject} sha256={digest}\nType the first {CONFIRM_LENGTH} characters of the digest to approve: ").strip().lower()
    if typed != digest[:CONFIRM_LENGTH]:
        raise ApprovalError("the confirmation does not match: nothing was approved")
    who = approver or current_person()
    store.add_approval(subject, action, digest, who, now)
    store.log("approval", f"{action} {digest[:12]} by {who}", subject if not subject.startswith("plan:") else None, now)


def require(store: Store, subject: str, action: str, digest: str, max_age_minutes: int, now: float | None = None) -> None:
    """Uses up one valid approval or raises; the caller must not run anything when this raises."""
    if not store.consume_approval(subject, action, digest, max_age_minutes * 60, now):
        raise ApprovalError("no valid approval for this exact recipe: approve it first (it expires and is single use)")
