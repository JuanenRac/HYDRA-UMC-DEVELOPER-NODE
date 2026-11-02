import json
from pathlib import Path

import pytest
from hydra_umc_developer_node import evidence
from hydra_umc_developer_node.settings import IngestSettings
from hydra_umc_developer_node.store import Store
from support import SECRET, make_bundle, make_message, write_json

NOW = 1_000_000.0
ENV = {"HYDRA_UMC_DEVELOPER_NODE_TRANSPORT_SECRET": SECRET}


def open_settings(**kw: object) -> IngestSettings:
    return IngestSettings(enabled=True, **kw)  # type: ignore[arg-type]


def test_a_valid_bundle_is_verified_and_gives_its_steps() -> None:
    assert evidence.verify_bundle(make_bundle())[0].startswith("systemctl")


def test_an_edited_bundle_is_refused() -> None:
    bundle = make_bundle()
    bundle["impact"] = "something else"
    with pytest.raises(evidence.EvidenceError, match="checksum"):
        evidence.verify_bundle(bundle)


def test_a_bundle_with_the_wrong_shape_is_refused() -> None:
    bundle = make_bundle()
    del bundle["impact"]
    with pytest.raises(evidence.EvidenceError, match="EvidenceBundle"):
        evidence.verify_bundle(bundle)
    with pytest.raises(evidence.EvidenceError):
        evidence.verify_bundle(make_bundle(reproductionSteps=[]))
    with pytest.raises(evidence.EvidenceError):
        evidence.verify_bundle(make_bundle(surprise=1))


def test_a_bundle_that_carries_a_secret_is_refused() -> None:
    with pytest.raises(evidence.EvidenceError, match="secret"):
        evidence.verify_bundle(make_bundle(redactedLogExcerpts=["password=hunter2hunter2"]))


def test_ingest_is_closed_by_default(tmp_path: Path) -> None:
    path = write_json(tmp_path / "b.json", make_bundle())
    with Store(tmp_path / "s.db") as store, pytest.raises(evidence.EvidenceError, match="closed"):
        evidence.ingest(path, IngestSettings(), store, ENV)
        raise AssertionError("not reached")
    with Store(tmp_path / "s.db") as store:
        assert store.list_cases() == []


def test_a_signed_message_becomes_a_case_waiting_for_review(tmp_path: Path) -> None:
    path = write_json(tmp_path / "m.json", make_message(make_bundle(), NOW))
    with Store(tmp_path / "s.db") as store:
        case_id, created = evidence.ingest(path, open_settings(), store, ENV, NOW)
        assert (case_id, created) == ("esc-1", True)
        assert store.get_case("esc-1")["status"] == "awaiting-review"
        assert store.journal(5)[0]["kind"] == "ingest"


def test_a_replayed_message_is_refused(tmp_path: Path) -> None:
    path = write_json(tmp_path / "m.json", make_message(make_bundle(), NOW))
    with Store(tmp_path / "s.db") as store:
        evidence.ingest(path, open_settings(), store, ENV, NOW)
        with pytest.raises(evidence.EvidenceError, match="replay"):
            evidence.ingest(path, open_settings(), store, ENV, NOW + 1)


def test_wrong_signature_receiver_age_and_secret(tmp_path: Path) -> None:
    with Store(tmp_path / "s.db") as store:
        forged = make_message(make_bundle(), NOW)
        forged["payload"]["escalationId"] = "other"
        for message, text in ((forged, "signature"), (make_message(make_bundle(), NOW, to_node="x"), "another node"),
                              (make_message(make_bundle(), NOW - 10_000, nonce="n-2"), "too old")):
            path = write_json(tmp_path / "m.json", message)
            with pytest.raises(evidence.EvidenceError, match=text):
                evidence.ingest(path, open_settings(), store, ENV, NOW)
        path = write_json(tmp_path / "m.json", make_message(make_bundle(), NOW, nonce="n-3"))
        with pytest.raises(evidence.EvidenceError, match="secret"):
            evidence.ingest(path, open_settings(), store, {}, NOW)
        assert store.list_cases() == []


def test_an_invalid_signature_does_not_use_up_the_nonce(tmp_path: Path) -> None:
    with Store(tmp_path / "s.db") as store:
        forged = make_message(make_bundle(), NOW, nonce="n-9")
        forged["mac"] = "0" * 64
        with pytest.raises(evidence.EvidenceError):
            evidence.verify_message(forged, open_settings(), SECRET, store, NOW)
        assert store.remember_nonce("n-9", 100, NOW)


def test_a_bare_bundle_needs_the_switch_that_allows_it(tmp_path: Path) -> None:
    path = write_json(tmp_path / "b.json", make_bundle())
    with Store(tmp_path / "s.db") as store:
        with pytest.raises(evidence.EvidenceError, match="requireTransportMac"):
            evidence.ingest(path, open_settings(), store, ENV, NOW)
        case_id, created = evidence.ingest(path, open_settings(require_transport_mac=False), store, ENV, NOW)
        assert created and case_id.startswith("bundle-")
        assert evidence.ingest(path, open_settings(require_transport_mac=False), store, ENV, NOW)[1] is False


def test_size_limit_and_bad_files(tmp_path: Path) -> None:
    path = write_json(tmp_path / "b.json", make_bundle())
    with Store(tmp_path / "s.db") as store:
        with pytest.raises(evidence.EvidenceError, match="bigger"):
            evidence.ingest(path, open_settings(max_bundle_bytes=10), store, ENV, NOW)
        (tmp_path / "bad.json").write_text("{")
        with pytest.raises(evidence.EvidenceError, match="JSON"):
            evidence.ingest(tmp_path / "bad.json", open_settings(), store, ENV, NOW)
        with pytest.raises(evidence.EvidenceError, match="cannot read"):
            evidence.ingest(tmp_path / "missing.json", open_settings(), store, ENV, NOW)


def test_an_escalation_id_must_be_a_plain_identifier(tmp_path: Path) -> None:
    path = write_json(tmp_path / "m.json", make_message(make_bundle(), NOW, escalation_id="../evil"))
    with Store(tmp_path / "s.db") as store, pytest.raises(evidence.EvidenceError, match="identifier"):
        evidence.ingest(path, open_settings(), store, ENV, NOW)


def test_the_secret_can_come_from_a_file(tmp_path: Path) -> None:
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(SECRET + "\n")
    assert evidence.read_secret(open_settings(secret_file=str(secret_file)), {}) == SECRET
    short = tmp_path / "short.txt"
    short.write_text("abc")
    with pytest.raises(evidence.EvidenceError):
        evidence.read_secret(open_settings(secret_file=str(short)), {})
    with pytest.raises(evidence.EvidenceError):
        evidence.read_secret(open_settings(secret_file=str(tmp_path / "none")), {})


def test_same_checksum_as_the_local_technician_when_it_is_next_to_this_repository() -> None:
    technician = Path(__file__).resolve().parents[2] / "HYDRA-UMC-LOCAL-TECHNICIAN" / "src"
    if not technician.is_dir():
        pytest.skip("the local technician is not checked out next to this repository")
    import sys

    sys.path.insert(0, str(technician))
    try:
        from hydra_umc_local_technician.escalation import evidence as theirs
    finally:
        sys.path.remove(str(technician))
    bundle = make_bundle()
    assert theirs.verify_bundle(bundle) == evidence.verify_bundle(bundle)
    assert json.dumps(bundle)  # the same document is accepted by both
