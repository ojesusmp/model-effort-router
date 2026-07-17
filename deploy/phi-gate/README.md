# phi-gate — deterministic PHI boundary gate (reference)

The load-bearing control of Design C: a deterministic decision function on every
boundary crossing toward a non-BAA model (GLM/DeepSeek). Never an LLM's judgment.

Contract (each clause is a test in `test_phi_gate.py`):

- Fail closed: findings, low confidence, detector errors, or a broken detector all
  route to the PHI lane; only an explicit clean verdict crosses.
- Tokenize-don't-redact: cleared text is de-identified via reversible tokenization
  (Cloud DLP deterministic/FPE in production); re-identification stays inside the
  BAA boundary.
- Every decision is audited (JSONL, no payloads) — the regulator-facing evidence.
- Tool outputs are crossings too: tag `source=tool_output:*` and gate them.

Run tests: `python3 -m pytest test_phi_gate.py -v`

**The bundled InMemoryDetector is test scaffolding, not a control.** Production
must call Google Cloud DLP (`content.inspect` / `content.deidentify`) inside your
BAA, with recall measured on free-text narrative and backed by Expert
Determination. Wire-up per host: OpenClaw — in front of the orchestrator binding
and on `sessions_spawn` payloads toward non-BAA agents; Hermes — mandatory
middleware in front of the brain.
