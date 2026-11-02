# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/evidence.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""Reading an evidence bundle of the local technician: check it, never change it, never run what it says.

A bundle comes either as a file of its own or inside an `incident-transport/1` message (a signed envelope). Both are checked the same
way before anything is stored: the shape (the EvidenceBundle contract), the checksum of the content (a file edited after it was
assembled is refused), and the absence of any secret shape. A transport message is checked first for its signature, its receiver, its
age and its nonce. What is stored is a case that waits for a person; reading a bundle starts no command.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .redaction import contains_secret
from .schema import SchemaError, validate
from .settings import IngestSettings
from .store import Store

CONTRACT_VERSION = "incident-transport/1"
MIN_SECRET_LENGTH = 24
_CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class EvidenceError(ValueError):
    """The bundle or the message is refused; the text says why and nothing was stored."""


def bundle_checksum(content: dict[str, Any]) -> str:
    """The checksum the technician computes: SHA-256 of the canonical JSON of the bundle without its `checksum` field."""
    canonical = json.dumps({key: value for key, value in content.items() if key != "checksum"}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_bundle(bundle: Any) -> list[str]:
    """Checks an EvidenceBundle (read only) and returns its reproduction steps. Raises `EvidenceError` when it is not trustworthy."""
    try:
        validate("evidence_bundle", bundle)
    except SchemaError as error:
        raise EvidenceError(f"the bundle is not a valid EvidenceBundle: {error}") from error
    if bundle_checksum(bundle) != bundle["checksum"]:
        raise EvidenceError("the checksum of the bundle is not that of its content: it was changed after it was assembled")
    if contains_secret(json.dumps(bundle, ensure_ascii=False)):
        raise EvidenceError("the bundle carries something that looks like a secret; it is refused instead of stored")
    return list(bundle["reproductionSteps"])


def read_secret(settings: IngestSettings, environ: Mapping[str, str]) -> str:
    """The shared secret of the transport: the file when one is configured, else the environment variable. Never from the command line."""
    if settings.secret_file:
        try:
            value = Path(settings.secret_file).read_text(encoding="utf-8").strip()
        except OSError as error:
            raise EvidenceError(f"cannot read the secret file: {error.strerror or 'error'}") from error
    else:
        value = environ.get(settings.secret_env, "").strip()
    if len(value) < MIN_SECRET_LENGTH:
        raise EvidenceError(f"the transport secret is missing or shorter than {MIN_SECRET_LENGTH} characters")
    return value


def _signing_bytes(body: dict[str, Any]) -> bytes:
    return json.dumps({key: value for key, value in body.items() if key != "mac"}, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_message(body: dict[str, Any], secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), _signing_bytes(body), hashlib.sha256).hexdigest()


def verify_message(message: Any, settings: IngestSettings, secret: str, store: Store, now: float | None = None) -> tuple[str, dict[str, Any]]:
    """Checks a signed `incident-transport/1` message and returns the case id and the bundle it carries."""
    moment = time.time() if now is None else now
    if not isinstance(message, dict):
        raise EvidenceError("the message is not a JSON object")
    mac = message.get("mac")
    if not isinstance(mac, str) or not hmac.compare_digest(mac, sign_message(message, secret)):
        raise EvidenceError("the signature of the message is wrong")
    if message.get("contract_version") != CONTRACT_VERSION or message.get("kind") != "incident":
        raise EvidenceError("the message is not an incident of incident-transport/1")
    if message.get("to_node") != settings.expected_to_node:
        raise EvidenceError("the message is addressed to another node")
    sent_at = message.get("sent_at")
    if isinstance(sent_at, bool) or not isinstance(sent_at, (int, float)) or abs(moment - sent_at) > settings.max_clock_skew_seconds:
        raise EvidenceError("the message is too old or too new")
    nonce = message.get("nonce")
    if not isinstance(nonce, str) or not nonce:
        raise EvidenceError("the message has no nonce")
    if not store.remember_nonce(nonce, settings.nonce_retention_seconds, moment):
        raise EvidenceError("the message was already received (replay)")
    payload = message.get("payload")
    if not isinstance(payload, dict) or not isinstance(payload.get("evidenceBundle"), dict):
        raise EvidenceError("the message carries no evidence bundle")
    case_id = payload.get("escalationId")
    if not isinstance(case_id, str) or not _CASE_ID.match(case_id):
        raise EvidenceError("the escalation id of the message is not a plain identifier")
    return case_id, payload["evidenceBundle"]


def ingest(path: Path, settings: IngestSettings, store: Store, environ: Mapping[str, str], now: float | None = None) -> tuple[str, bool]:
    """Reads a bundle file or a transport message file, checks it and stores it as a case that waits for review.

    Returns the case id and whether it was new. Refused when the `ingest` switch is closed.
    """
    if not settings.enabled:
        raise EvidenceError("ingest is closed: set ingest.enabled to true in the configuration file")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise EvidenceError(f"cannot read the file: {error.strerror or 'error'}") from error
    if size > settings.max_bundle_bytes:
        raise EvidenceError("the file is bigger than ingest.maxBundleBytes")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise EvidenceError(f"cannot read the file: {error.strerror or 'error'}") from error
    except ValueError as error:
        raise EvidenceError("the file is not valid JSON") from error
    if isinstance(document, dict) and "mac" in document:
        case_id, bundle = verify_message(document, settings, read_secret(settings, environ), store, now)
        source = "transport"
    else:
        if settings.require_transport_mac:
            raise EvidenceError("a bare bundle is refused: ingest.requireTransportMac is on and the file carries no signed message")
        bundle = document
        case_id = ""
        source = "file"
    verify_bundle(bundle)
    if not case_id:
        case_id = "bundle-" + bundle["checksum"][:16]
    created = store.add_case(case_id, source, bundle, now)
    store.log("ingest" if created else "ingest-duplicate", f"{source} bundle {bundle['checksum'][:12]}", case_id, now)
    return case_id, created
