"""phi-gate — deterministic PHI boundary gate (reference implementation).

Design C's load-bearing control: a deterministic decision function that sits on
every boundary crossing toward a NON-BAA model (GLM, DeepSeek). It never relies
on an LLM's judgment. Properties, enforced by tests in test_phi_gate.py:

  1. FAIL CLOSED: any detector finding, any low-confidence span, any detector
     error/timeout, or any empty/None verdict → route PHI_LANE. Only an explicit,
     healthy, zero-finding verdict routes CLEAR.
  2. TOKENIZE, DON'T JUST REDACT: when a de-identifier is provided, cleared
     crossings carry tokenized text; re-identification happens only inside the
     BAA boundary (detokenize() is never exposed on the non-BAA path).
  3. EVERY DECISION IS LOGGED: append-only JSONL audit records (verdict, info
     types, route, detector health) — the evidence a regulator sees.

Production detector: Google Cloud DLP (content.inspect / content.deidentify with
deterministic or format-preserving encryption), called inside your BAA. The
InMemoryDetector here exists ONLY so the gate's routing semantics are testable;
it must never be used as the production control.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Protocol


class Route(str, Enum):
    PHI_LANE = "phi_lane"   # BAA-covered lane (Vertex Flash/Pro)
    CLEAR = "clear"         # may cross to non-BAA models (GLM/DeepSeek)


class Verdict(str, Enum):
    CLEAN = "clean"
    PHI = "phi"
    ERROR = "error"


@dataclass
class InspectionResult:
    verdict: Verdict
    info_types: list[str] = field(default_factory=list)
    # Detector-reported confidence for the *clean* claim. Anything below the
    # threshold is treated as PHI (fail closed).
    confidence: float = 1.0
    error: Optional[str] = None


class Detector(Protocol):
    def inspect(self, text: str) -> InspectionResult: ...


@dataclass
class GateDecision:
    route: Route
    verdict: Verdict
    info_types: list[str]
    reason: str
    # Text that may cross the boundary. ONLY set when route == CLEAR.
    # If a deidentifier was configured, this is the tokenized form.
    outbound_text: Optional[str] = None


class PhiGate:
    """Deterministic routing decision for one boundary crossing."""

    def __init__(
        self,
        detector: Detector,
        audit_path: str,
        min_clean_confidence: float = 0.99,
        deidentify: Optional[Callable[[str], str]] = None,
    ):
        self._detector = detector
        self._audit_path = audit_path
        self._min_clean_confidence = min_clean_confidence
        self._deidentify = deidentify

    def decide(self, text: str, *, source: str = "ingress") -> GateDecision:
        try:
            result = self._detector.inspect(text)
        except Exception as exc:  # detector crashed → fail closed
            result = InspectionResult(
                verdict=Verdict.ERROR, error=f"{type(exc).__name__}: {exc}"
            )

        if result is None:  # defensive: a broken detector returning nothing
            result = InspectionResult(verdict=Verdict.ERROR, error="detector returned None")

        decision = self._route(result, text)
        self._audit(decision, result, source)
        return decision

    def _route(self, result: InspectionResult, text: str) -> GateDecision:
        if result.verdict is Verdict.ERROR:
            return GateDecision(
                route=Route.PHI_LANE,
                verdict=Verdict.ERROR,
                info_types=[],
                reason=f"fail-closed: detector error ({result.error})",
            )
        if result.verdict is Verdict.PHI or result.info_types:
            return GateDecision(
                route=Route.PHI_LANE,
                verdict=Verdict.PHI,
                info_types=list(result.info_types),
                reason="fail-closed: findings present",
            )
        if result.confidence < self._min_clean_confidence:
            return GateDecision(
                route=Route.PHI_LANE,
                verdict=Verdict.PHI,
                info_types=[],
                reason=(
                    f"fail-closed: clean confidence {result.confidence:.3f} "
                    f"< {self._min_clean_confidence}"
                ),
            )
        outbound = self._deidentify(text) if self._deidentify else text
        return GateDecision(
            route=Route.CLEAR,
            verdict=Verdict.CLEAN,
            info_types=[],
            reason="explicit clean verdict at required confidence",
            outbound_text=outbound,
        )

    def _audit(self, decision: GateDecision, result: InspectionResult, source: str) -> None:
        record = {
            "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": source,
            "route": decision.route.value,
            "verdict": decision.verdict.value,
            "info_types": decision.info_types,
            "reason": decision.reason,
            "detector_error": result.error,
        }
        # Append-only; never contains the payload itself.
        with open(self._audit_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Test-only detector. NOT a production control: real deployments call Google
# Cloud DLP inside the BAA. This exists so the gate's fail-closed semantics can
# be unit-tested without network access.
# ---------------------------------------------------------------------------

_TEST_PATTERNS = {
    "US_SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "MRN": re.compile(r"\bMRN[:\s]*\d{6,10}\b", re.IGNORECASE),
    "DOB": re.compile(r"\bDOB[:\s]*\d{1,2}/\d{1,2}/\d{2,4}\b", re.IGNORECASE),
    "PHONE": re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b"),
}


class InMemoryDetector:
    def __init__(self, fail: bool = False, clean_confidence: float = 1.0):
        self._fail = fail
        self._clean_confidence = clean_confidence

    def inspect(self, text: str) -> InspectionResult:
        if self._fail:
            raise RuntimeError("simulated detector outage")
        hits = [name for name, rx in _TEST_PATTERNS.items() if rx.search(text)]
        if hits:
            return InspectionResult(verdict=Verdict.PHI, info_types=hits)
        return InspectionResult(verdict=Verdict.CLEAN, confidence=self._clean_confidence)
