"""Tests for the phi-gate fail-closed properties.

Each test encodes one clause of the Design C contract. If any of these fail,
the gate is not safe to put on the GLM/DeepSeek boundary.
"""

import json

import pytest

from phi_gate import (
    GateDecision,
    InMemoryDetector,
    InspectionResult,
    PhiGate,
    Route,
    Verdict,
)


@pytest.fixture()
def audit(tmp_path):
    return str(tmp_path / "audit.jsonl")


def read_audit(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def test_clean_text_routes_clear(audit):
    gate = PhiGate(InMemoryDetector(), audit)
    d = gate.decide("Summarize the Q3 deployment runbook for the ops team.")
    assert d.route is Route.CLEAR
    assert d.outbound_text is not None


def test_ssn_routes_phi_lane(audit):
    gate = PhiGate(InMemoryDetector(), audit)
    d = gate.decide("Patient SSN 123-45-6789 needs a claim review.")
    assert d.route is Route.PHI_LANE
    assert "US_SSN" in d.info_types
    assert d.outbound_text is None  # nothing crosses the boundary


def test_mrn_and_dob_route_phi_lane(audit):
    gate = PhiGate(InMemoryDetector(), audit)
    d = gate.decide("Chart MRN: 88123456, DOB: 4/12/1961, abnormal labs flagged.")
    assert d.route is Route.PHI_LANE
    assert set(d.info_types) >= {"MRN", "DOB"}


def test_detector_exception_fails_closed(audit):
    gate = PhiGate(InMemoryDetector(fail=True), audit)
    d = gate.decide("Totally innocuous text about the weather.")
    assert d.route is Route.PHI_LANE  # outage ≠ clean
    assert d.verdict is Verdict.ERROR
    assert d.outbound_text is None


def test_detector_returning_none_fails_closed(audit):
    class NoneDetector:
        def inspect(self, text):
            return None

    gate = PhiGate(NoneDetector(), audit)
    d = gate.decide("anything")
    assert d.route is Route.PHI_LANE
    assert d.verdict is Verdict.ERROR


def test_low_confidence_clean_fails_closed(audit):
    gate = PhiGate(InMemoryDetector(clean_confidence=0.90), audit, min_clean_confidence=0.99)
    d = gate.decide("Ambiguous free-text narrative with no obvious identifiers.")
    assert d.route is Route.PHI_LANE  # doubt defaults to PHI


def test_findings_override_clean_verdict(audit):
    """A detector that self-contradicts (clean verdict but findings listed) must fail closed."""

    class ContradictoryDetector:
        def inspect(self, text):
            return InspectionResult(verdict=Verdict.CLEAN, info_types=["US_SSN"])

    gate = PhiGate(ContradictoryDetector(), audit)
    d = gate.decide("whatever")
    assert d.route is Route.PHI_LANE


def test_tokenization_applied_only_on_clear(audit):
    tokenize = lambda s: s.replace("Orlando", "PERSON_TOKEN_1")
    gate = PhiGate(InMemoryDetector(), audit, deidentify=tokenize)
    d = gate.decide("Orlando asked for the deployment summary.")
    assert d.route is Route.CLEAR
    assert d.outbound_text == "PERSON_TOKEN_1 asked for the deployment summary."

    d2 = gate.decide("Orlando's patient, SSN 123-45-6789.")
    assert d2.route is Route.PHI_LANE
    assert d2.outbound_text is None  # tokenizer never runs on the PHI path outbound


def test_every_decision_is_audited_without_payload(audit):
    gate = PhiGate(InMemoryDetector(), audit)
    gate.decide("clean text one")
    gate.decide("SSN 123-45-6789")
    records = read_audit(audit)
    assert len(records) == 2
    assert records[0]["route"] == "clear"
    assert records[1]["route"] == "phi_lane"
    # The audit log must never contain the payload itself.
    raw = open(audit, encoding="utf-8").read()
    assert "clean text one" not in raw
    assert "123-45-6789" not in raw


def test_tool_output_source_is_recorded(audit):
    """Mid-task tool output is a boundary crossing too — the source tag proves coverage."""
    gate = PhiGate(InMemoryDetector(), audit)
    gate.decide("file contents with MRN: 8812345678", source="tool_output:file_read")
    rec = read_audit(audit)[0]
    assert rec["source"] == "tool_output:file_read"
    assert rec["route"] == "phi_lane"
