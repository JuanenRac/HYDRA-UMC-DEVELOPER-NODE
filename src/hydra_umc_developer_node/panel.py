# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/panel.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The status document a dashboard or a studio shows: switches, queue, journal and health (contract `developer-node-status/1`).

The node only writes this document; a reader only reads it. There is no command channel in it and this module opens no port: whoever
shows it (HYDRA-UMC-DASHBOARD-AI, STUDIO) fetches the file through its own authenticated path. It carries counts, kinds and short
details, never a bundle, a recipe or any output of a command.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from . import __version__, i18n, plugin_ci
from .checkouts import CheckoutCache
from .schema import validate
from .settings import Settings
from .store import Store


class PanelError(ValueError):
    """The panel is closed."""


def build_status(settings: Settings, store: Store, now: float | None = None) -> dict[str, Any]:
    if not settings.panel.enabled:
        raise PanelError("panel is closed: set panel.enabled to true in the configuration file")
    moment = time.time() if now is None else now
    cache = CheckoutCache(settings.checkouts, settings.data_path())
    cache_bytes = cache.size_bytes()
    report = plugin_ci.latest_report(settings.data_path())
    last_report = None
    if report is not None and isinstance(report.get("summary"), dict):
        last_report = {"finished_at": report.get("finished_at"), "summary": report["summary"]}
    status: dict[str, Any] = {
        "contract": "developer-node-status/1",
        "version": __version__,
        "language": settings.language,
        "generated_at": moment,
        "switches": settings.switches(),
        "queue": {
            "cases": store.case_counts(),
            "awaiting_approval": store.pending_approvals(settings.repro.approval_max_age_minutes * 60, moment),
            "outcomes": store.outcome_count(),
        },
        "journal": store.journal(settings.panel.max_journal_entries),
        "health": {
            "store_ok": store.integrity_ok(),
            "cache_bytes": cache_bytes,
            "cache_limit_bytes": settings.checkouts.max_cache_bytes,
            "cache_over_limit": cache_bytes > settings.checkouts.max_cache_bytes,
            "last_ci_report": last_report,
        },
        "labels": i18n.labels(settings.language),
    }
    validate("panel_status", status)
    return status


def export_status(settings: Settings, store: Store, now: float | None = None) -> Path:
    """Writes the status document to `<dataDir>/panel/status.json` (a temporary file and a rename, so a reader never sees half of it)."""
    status = build_status(settings, store, now)
    folder = settings.data_path() / "panel"
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder / "status.json.tmp"
    temporary.write_text(json.dumps(status, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    target = folder / "status.json"
    os.replace(temporary, target)
    return target
