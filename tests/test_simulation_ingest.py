"""Simulation bench: a stream of signed messages from simulated technician nodes with injected faults (replays, tampering, a
wrong secret, clock skew, a wrong destination) drawn from a fixed seed. Only the good, new ones may be accepted. No node, no network."""
import random
from pathlib import Path
from typing import Any

from hydra_umc_developer_node import evidence
from hydra_umc_developer_node.settings import IngestSettings
from hydra_umc_developer_node.store import Store
from support import SECRET, make_bundle, make_message

NOW = 2_000_000.0
SETTINGS = IngestSettings(enabled=True)


def _stream(seed: int, count: int) -> list[tuple[dict[str, Any], bool]]:
    """(message, should it be accepted). A fault makes a message wrong; a replay repeats an earlier good one."""
    rng = random.Random(seed)
    out: list[tuple[dict[str, Any], bool]] = []
    good: list[dict[str, Any]] = []
    for index in range(count):
        fault = rng.choice(["none", "none", "none", "replay", "tamper", "secret", "skew", "node", "bundle"])
        if fault == "replay" and not good:
            fault = "none"
        if fault == "replay":
            out.append((dict(rng.choice(good)), False))
            continue
        message = make_message(make_bundle(impact=f"case {index}"), NOW + rng.randint(-60, 60), nonce=f"n-{seed}-{index}", escalation_id=f"esc-{index}")
        if fault == "tamper":
            message["payload"]["escalationId"] = f"evil-{index}"
        elif fault == "secret":
            message["mac"] = evidence.sign_message(message, "y" * 32)
        elif fault == "skew":
            message["sent_at"] = NOW + rng.choice([-1, 1]) * 4000
            message["mac"] = evidence.sign_message(message, SECRET)
        elif fault == "node":
            message["to_node"] = "someone-else"
            message["mac"] = evidence.sign_message(message, SECRET)
        elif fault == "bundle":
            message["payload"]["evidenceBundle"]["impact"] = "edited after the checksum"
            message["mac"] = evidence.sign_message(message, SECRET)
        else:
            good.append(message)
        out.append((message, fault == "none"))
    return out


def _ingest(message: dict[str, Any], store: Store) -> bool:
    try:
        _case, bundle = evidence.verify_message(message, SETTINGS, SECRET, store, NOW)
        evidence.verify_bundle(bundle)
    except evidence.EvidenceError:
        return False
    return True


def test_only_good_new_messages_are_accepted_from_300_simulated_ones(tmp_path: Path) -> None:
    accepted_total = refused_total = 0
    for seed in (1, 5, 99):
        with Store(tmp_path / f"s{seed}.db") as store:
            seen: set[str] = set()
            for message, expected in _stream(seed, 100):
                got = _ingest(message, store)
                assert got == expected, (seed, message["payload"].get("escalationId"), message["nonce"])
                if got:
                    assert message["nonce"] not in seen  # a nonce is accepted once
                    seen.add(message["nonce"])
                    accepted_total += 1
                else:
                    refused_total += 1
    assert accepted_total > 50 and refused_total > 50  # the draw reaches both sides


def test_the_same_seed_gives_the_same_stream(tmp_path: Path) -> None:
    def run(name: str) -> list[bool]:
        with Store(tmp_path / name) as store:
            return [_ingest(message, store) for message, _ in _stream(7, 60)]

    assert run("a.db") == run("b.db")
