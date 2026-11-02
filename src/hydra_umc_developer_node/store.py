# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - src/hydra_umc_developer_node/store.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""The local SQLite file of the node: cases, the append-only journal, approvals, run outcomes and the nonces already seen.

Everything stays on this machine. The journal is only ever appended to (no function here updates or deletes a journal row), so what the
node did can be read back in order. Every statement uses bound parameters.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    checksum TEXT NOT NULL,
    bundle TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at REAL NOT NULL,
    kind TEXT NOT NULL,
    case_id TEXT,
    detail TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    action TEXT NOT NULL,
    digest TEXT NOT NULL,
    approver TEXT NOT NULL,
    created_at REAL NOT NULL,
    used_at REAL
);
CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    run_id TEXT NOT NULL,
    document TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nonces (
    nonce TEXT PRIMARY KEY,
    seen_at REAL NOT NULL
);
"""


class StoreError(ValueError):
    """The store refuses the operation (an unknown case, a duplicate)."""


class Store:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), timeout=10, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------ journal
    def log(self, kind: str, detail: str, case_id: str | None = None, now: float | None = None) -> None:
        self._db.execute("INSERT INTO journal (at, kind, case_id, detail) VALUES (?, ?, ?, ?)",
                         (time.time() if now is None else now, kind, case_id, detail[:2000]))

    def journal(self, limit: int) -> list[dict[str, Any]]:
        rows = self._db.execute("SELECT id, at, kind, case_id, detail FROM journal ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------ cases
    def add_case(self, case_id: str, source: str, bundle: dict[str, Any], now: float | None = None) -> bool:
        """Stores a verified bundle as a case waiting for a person. Returns False (and stores nothing) when the case already exists."""
        try:
            self._db.execute(
                "INSERT INTO cases (id, created_at, source, status, checksum, bundle) VALUES (?, ?, ?, 'awaiting-review', ?, ?)",
                (case_id, time.time() if now is None else now, source, bundle["checksum"], json.dumps(bundle, sort_keys=True)))
        except sqlite3.IntegrityError:
            return False
        return True

    def get_case(self, case_id: str) -> dict[str, Any]:
        row = self._db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            raise StoreError(f"unknown case {case_id!r}")
        case = dict(row)
        case["bundle"] = json.loads(case["bundle"])
        return case

    def list_cases(self) -> list[dict[str, Any]]:
        rows = self._db.execute("SELECT id, created_at, source, status, checksum FROM cases ORDER BY created_at, id").fetchall()
        return [dict(row) for row in rows]

    def set_status(self, case_id: str, status: str) -> None:
        self.get_case(case_id)
        self._db.execute("UPDATE cases SET status = ? WHERE id = ?", (status, case_id))

    def case_counts(self) -> dict[str, int]:
        rows = self._db.execute("SELECT status, COUNT(*) AS n FROM cases GROUP BY status").fetchall()
        return {row["status"]: row["n"] for row in rows}

    # ------------------------------------------------------------------ approvals
    def add_approval(self, subject: str, action: str, digest: str, approver: str, now: float | None = None) -> None:
        self._db.execute("INSERT INTO approvals (subject, action, digest, approver, created_at) VALUES (?, ?, ?, ?, ?)",
                         (subject, action, digest, approver, time.time() if now is None else now))

    def consume_approval(self, subject: str, action: str, digest: str, max_age_seconds: float, now: float | None = None) -> bool:
        """Marks the newest unused, unexpired approval for exactly this subject, action and digest as used. True when there was one."""
        moment = time.time() if now is None else now
        row = self._db.execute(
            "SELECT id FROM approvals WHERE subject = ? AND action = ? AND digest = ? AND used_at IS NULL AND created_at >= ? "
            "ORDER BY id DESC LIMIT 1", (subject, action, digest, moment - max_age_seconds)).fetchone()
        if row is None:
            return False
        self._db.execute("UPDATE approvals SET used_at = ? WHERE id = ?", (moment, row["id"]))
        return True

    def pending_approvals(self, max_age_seconds: float, now: float | None = None) -> int:
        moment = time.time() if now is None else now
        row = self._db.execute("SELECT COUNT(*) AS n FROM approvals WHERE used_at IS NULL AND created_at >= ?",
                               (moment - max_age_seconds,)).fetchone()
        return int(row["n"])

    # ------------------------------------------------------------------ outcomes
    def add_outcome(self, case_id: str, outcome: dict[str, Any]) -> None:
        self._db.execute("INSERT INTO outcomes (case_id, scenario_id, phase, run_id, document) VALUES (?, ?, ?, ?, ?)",
                         (case_id, outcome["scenario_id"], outcome["phase"], outcome["run_id"], json.dumps(outcome, sort_keys=True)))

    def latest_outcome(self, case_id: str, scenario_id: str, phase: str) -> dict[str, Any] | None:
        row = self._db.execute("SELECT document FROM outcomes WHERE case_id = ? AND scenario_id = ? AND phase = ? ORDER BY id DESC LIMIT 1",
                               (case_id, scenario_id, phase)).fetchone()
        if row is None:
            return None
        loaded = json.loads(row["document"])
        return loaded if isinstance(loaded, dict) else None

    def outcome_count(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) AS n FROM outcomes").fetchone()["n"])

    # ------------------------------------------------------------------ nonces
    def remember_nonce(self, nonce: str, retention_seconds: float, now: float | None = None) -> bool:
        """False when the nonce was already seen inside the retention window (a replayed message)."""
        moment = time.time() if now is None else now
        self._db.execute("DELETE FROM nonces WHERE seen_at < ?", (moment - retention_seconds,))
        try:
            self._db.execute("INSERT INTO nonces (nonce, seen_at) VALUES (?, ?)", (nonce, moment))
        except sqlite3.IntegrityError:
            return False
        return True

    def integrity_ok(self) -> bool:
        try:
            return self._db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        except sqlite3.DatabaseError:
            return False
