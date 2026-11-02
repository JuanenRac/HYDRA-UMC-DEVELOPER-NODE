# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/redaction.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Secret shapes: redact the output of the commands the node runs, and refuse a document that already carries one."""
from __future__ import annotations

import re

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)", re.DOTALL),
    re.compile(r"(?i)\b(authorization|proxy-authorization)\s*[:=]\s*(bearer|basic|token)\s+\S+"),
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key|access[_-]?key)\b\s*[:=]\s*\S+"),
    re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@"),
)
MASK = "[redacted]"


def redact(text: str) -> str:
    """The text with every secret shape replaced by a mask; text without one comes back unchanged."""
    for pattern in _PATTERNS:
        text = pattern.sub(MASK, text)
    return text


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PATTERNS)
