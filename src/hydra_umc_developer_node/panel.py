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
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import __version__, i18n, plugin_ci, plugin_full
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
    full_report = plugin_full.latest_report(settings.data_path())
    last_full = None
    if full_report is not None and isinstance(full_report.get("summary"), dict):
        last_full = {"finished_at": full_report.get("finished_at"), "aborted": full_report.get("aborted"), "summary": full_report["summary"]}
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
            "last_ci_full_report": last_full,
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


class PushError(PanelError):
    """The status document could not be handed to the server."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is never followed: the token would travel to a place the operator did not name."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def _push_token(settings: Settings) -> str:
    push = settings.server_push
    token = ""
    if push.token_file:
        try:
            token = Path(push.token_file).expanduser().read_text(encoding="utf-8").strip()
        except OSError as error:
            raise PushError(f"cannot read serverPush.tokenFile: {error.strerror or 'error'}") from error
    elif push.token_env:
        token = os.environ.get(push.token_env, "").strip()
    if len(token) < 16:
        raise PushError("the token of this node is missing or too short (serverPush.tokenEnv or serverPush.tokenFile)")
    return token


def _push_url(settings: Settings) -> str:
    push = settings.server_push
    parsed = urllib.parse.urlparse(push.url)
    loopback = parsed.hostname in ("127.0.0.1", "localhost", "::1")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise PushError("serverPush.url must be an https URL (plain http is accepted only for this machine)")
    if not parsed.hostname or parsed.username or parsed.password:
        raise PushError("serverPush.url must name a host and carry no credentials")
    return push.url.rstrip("/") + "/api/ingest/developer-node/status"


def push_status(settings: Settings, store: Store, now: float | None = None) -> dict[str, Any]:
    """Sends the status document to HYDRA-UMC-SERVER with the token of this node. Off unless `serverPush.enabled`; HTTPS only (a plain
    http URL is accepted for this machine alone); a redirect is not followed; the token is never printed or put in an error."""
    push = settings.server_push
    if not push.enabled:
        raise PanelError("serverPush is closed: set serverPush.enabled to true in the configuration file")
    if not push.node_id:
        raise PushError("serverPush.nodeId is empty")
    url = _push_url(settings)
    token = _push_token(settings)
    body = json.dumps(build_status(settings, store, now), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {token}", "X-Node-Id": push.node_id,
    })
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=push.timeout_seconds) as response:
            answer = json.loads(response.read(65536) or b"{}")
            return {"status": response.status, "answer": answer}
    except urllib.error.HTTPError as error:
        raise PushError(f"the server refused the status document ({error.code})") from None
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise PushError(f"the server could not be reached: {type(error).__name__}") from None
