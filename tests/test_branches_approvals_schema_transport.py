"""Branches that were not covered: the approval gate, the small schema checker and every refusal of a signed transport message."""
import io
from pathlib import Path
from typing import Any

import pytest
from hydra_umc_developer_node import approvals, evidence, schema
from hydra_umc_developer_node.settings import IngestSettings
from hydra_umc_developer_node.store import Store
from support import SECRET, make_bundle, make_message

NOW = 1_000_000.0
SETTINGS = IngestSettings(enabled=True)


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


# ---- approvals --------------------------------------------------------------------------------------------------------------

def test_the_digest_is_stable_and_ignores_key_order() -> None:
    assert approvals.digest_of({"a": 1, "b": [1, 2]}) == approvals.digest_of({"b": [1, 2], "a": 1})
    assert approvals.digest_of({"a": 1}) != approvals.digest_of({"a": 2})


def test_input_that_is_not_a_terminal_approves_nothing(tmp_path: Path) -> None:
    with Store(tmp_path / "s.db") as store:
        with pytest.raises(approvals.ApprovalError, match="terminal"):
            approvals.approve(store, "case-1", "repro", "a" * 64, stream=io.StringIO())
        with pytest.raises(approvals.ApprovalError):
            approvals.require(store, "case-1", "repro", "a" * 64, 10, now=NOW)


def test_a_wrong_or_empty_confirmation_approves_nothing(tmp_path: Path) -> None:
    digest = approvals.digest_of({"cmd": "x"})
    with Store(tmp_path / "s.db") as store:
        for typed in ("", "   ", "zzzzzzzz", digest[:7]):
            with pytest.raises(approvals.ApprovalError, match="does not match"):
                approvals.approve(store, "case-1", "repro", digest, prompt=lambda _text, typed=typed: typed)
        with pytest.raises(approvals.ApprovalError):
            approvals.require(store, "case-1", "repro", digest, 10, now=NOW)


def test_the_confirmation_is_case_insensitive_and_the_approval_is_single_use(tmp_path: Path) -> None:
    digest = approvals.digest_of({"cmd": "x"})
    with Store(tmp_path / "s.db") as store:
        approvals.approve(store, "case-1", "repro", digest, prompt=lambda _text: digest[:8].upper(), approver="Ann", now=NOW)
        approvals.require(store, "case-1", "repro", digest, 10, now=NOW + 5)
        with pytest.raises(approvals.ApprovalError):
            approvals.require(store, "case-1", "repro", digest, 10, now=NOW + 6)


def test_an_approval_expires_and_is_bound_to_its_subject_action_and_digest(tmp_path: Path) -> None:
    digest = approvals.digest_of({"cmd": "x"})
    with Store(tmp_path / "s.db") as store:
        approvals.approve(store, "case-1", "repro", digest, prompt=lambda _text: digest[:8], approver="Ann", now=NOW)
        for subject, action, wanted in (("case-2", "repro", digest), ("case-1", "ci", digest), ("case-1", "repro", "b" * 64)):
            with pytest.raises(approvals.ApprovalError):
                approvals.require(store, subject, action, wanted, 10, now=NOW + 1)
        with pytest.raises(approvals.ApprovalError):
            approvals.require(store, "case-1", "repro", digest, 10, now=NOW + 601)  # past the 10 minutes
        approvals.require(store, "case-1", "repro", digest, 10, now=NOW + 599)  # still inside, nothing was spent above


def test_a_terminal_stream_is_accepted_when_a_prompt_is_given(tmp_path: Path) -> None:
    digest = approvals.digest_of({"plan": 1})
    with Store(tmp_path / "s.db") as store:
        approvals.approve(store, "plan:p1", "ci", digest, prompt=lambda _text: digest[:8], stream=_Tty(), approver="Bo", now=NOW)
        approvals.require(store, "plan:p1", "ci", digest, 10, now=NOW)


# ---- schema -----------------------------------------------------------------------------------------------------------------

def check(value: Any, schema_: dict[str, Any]) -> None:
    schema._check(value, schema_, "$")


@pytest.mark.parametrize("value, schema_", [
    (5, {"const": 4}), ("c", {"enum": ["a", "b"]}), ("x", {"type": "integer"}), (True, {"type": "integer"}), (True, {"type": "number"}),
    ("", {"type": "string", "minLength": 1}), (1, {"type": "integer", "minimum": 2}), ([], {"type": "array", "minItems": 1}),
    ([1, "a"], {"type": "array", "items": {"type": "integer"}}), ({}, {"type": "object", "required": ["k"]}),
    ({"k": 1, "z": 2}, {"type": "object", "additionalProperties": False, "properties": {"k": {}}}),
    ({"k": 1, "z": "s"}, {"type": "object", "properties": {"k": {}}, "additionalProperties": {"type": "integer"}}),
    (None, {"type": ["string", "integer"]}),
])
def test_a_document_that_breaks_the_contract_is_refused(value: Any, schema_: dict[str, Any]) -> None:
    with pytest.raises(schema.SchemaError):
        check(value, schema_)


@pytest.mark.parametrize("value, schema_", [
    (4, {"const": 4}), ("a", {"enum": ["a", "b"]}), (2.5, {"type": "number"}), (None, {"type": ["null", "string"]}),
    ("x", {"type": "string", "minLength": 1}), (3, {"type": "integer", "minimum": 3}), ([1, 2], {"type": "array", "items": {"type": "integer"}}),
    ({"k": 1, "z": 2}, {"type": "object", "required": ["k"], "additionalProperties": {"type": "integer"}, "properties": {"k": {}}}),
    ({"anything": 1}, {"type": "object"}), ("any", {"description": "annotations are ignored"}),
])
def test_a_document_that_keeps_the_contract_passes(value: Any, schema_: dict[str, Any]) -> None:
    check(value, schema_)


def test_the_error_names_the_path_of_the_fault() -> None:
    with pytest.raises(schema.SchemaError, match=r"\$\.items\[1\]"):
        check({"items": [1, "a"]}, {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "integer"}}}})


def test_an_unknown_type_in_a_contract_is_an_error_never_a_silent_pass() -> None:
    with pytest.raises(schema.SchemaError, match="unknown type"):
        check(1, {"type": "decimal"})


def test_a_missing_contract_cannot_be_read() -> None:
    with pytest.raises(schema.SchemaError, match="cannot read"):
        schema.load_contract("there-is-no-such-contract")


# ---- signed transport message -----------------------------------------------------------------------------------------------

def resign(message: dict[str, Any]) -> dict[str, Any]:
    message["mac"] = evidence.sign_message(message, SECRET)
    return message


def verify(message: Any, store: Store, settings: IngestSettings = SETTINGS) -> tuple[str, dict[str, Any]]:
    return evidence.verify_message(message, settings, SECRET, store, NOW)


def test_a_valid_message_gives_its_case_and_bundle(tmp_path: Path) -> None:
    bundle = make_bundle()
    with Store(tmp_path / "s.db") as store:
        case_id, carried = verify(make_message(bundle, NOW), store)
    assert (case_id, carried) == ("esc-1", bundle)


def test_every_malformed_message_is_refused_with_its_own_reason(tmp_path: Path) -> None:
    counter = iter(range(1000))

    def edited(**changes: Any) -> dict[str, Any]:
        message = make_message(make_bundle(), NOW, nonce=f"nonce-{next(counter)}")
        for key, value in changes.items():
            if value is None:
                message.pop(key, None)
            else:
                message[key] = value
        return resign(message)

    def payload_without(key: str) -> dict[str, Any]:
        message = make_message(make_bundle(), NOW, nonce=f"nonce-{next(counter)}")
        message["payload"].pop(key)
        return resign(message)

    cases = [
        (["not", "an", "object"], "not a JSON object"),
        (edited(contract_version="incident-transport/9"), "incident-transport/1"),
        (edited(kind="status"), "incident-transport/1"),
        (edited(to_node="another-node"), "another node"),
        (edited(sent_at=NOW - 301), "too old"),
        (edited(sent_at=NOW + 301), "too old"),
        (edited(sent_at="now"), "too old"),
        (edited(sent_at=True), "too old"),
        (edited(nonce=""), "no nonce"),
        (edited(nonce=5), "no nonce"),
        (edited(payload="text"), "no evidence bundle"),
        (payload_without("evidenceBundle"), "no evidence bundle"),
        (payload_without("escalationId"), "plain identifier"),
    ]
    with Store(tmp_path / "s.db") as store:
        for message, reason in cases:
            with pytest.raises(evidence.EvidenceError, match=reason):
                verify(message, store)


def test_a_message_edited_after_signing_or_signed_with_another_secret_is_refused(tmp_path: Path) -> None:
    with Store(tmp_path / "s.db") as store:
        message = make_message(make_bundle(), NOW)
        message["to_node"] = "developer-node "  # changed after the signature
        with pytest.raises(evidence.EvidenceError, match="signature"):
            verify(message, store)
        message = make_message(make_bundle(), NOW)
        message["mac"] = evidence.sign_message(message, "y" * 32)
        with pytest.raises(evidence.EvidenceError, match="signature"):
            verify(message, store)
        message = make_message(make_bundle(), NOW)
        message.pop("mac")
        with pytest.raises(evidence.EvidenceError, match="signature"):
            verify(message, store)


@pytest.mark.parametrize("case_id", ["../etc", "a/b", "-starts-with-dash", "", "x" * 81, "white space"])
def test_a_case_id_that_could_leave_the_work_folder_is_refused(tmp_path: Path, case_id: str) -> None:
    message = make_message(make_bundle(), NOW, escalation_id=case_id)
    with Store(tmp_path / "s.db") as store, pytest.raises(evidence.EvidenceError, match="plain identifier"):
        verify(message, store)


def test_a_replayed_message_is_refused_but_a_new_nonce_is_not(tmp_path: Path) -> None:
    with Store(tmp_path / "s.db") as store:
        verify(make_message(make_bundle(), NOW, nonce="once"), store)
        with pytest.raises(evidence.EvidenceError, match="replay"):
            verify(make_message(make_bundle(), NOW, nonce="once"), store)
        verify(make_message(make_bundle(), NOW, nonce="twice"), store)


def test_the_clock_skew_window_comes_from_the_settings(tmp_path: Path) -> None:
    tight = IngestSettings(enabled=True, max_clock_skew_seconds=10)
    with Store(tmp_path / "s.db") as store:
        with pytest.raises(evidence.EvidenceError, match="too old"):
            verify(make_message(make_bundle(), NOW - 11, nonce="a"), store, tight)
        verify(make_message(make_bundle(), NOW - 9, nonce="b"), store, tight)
