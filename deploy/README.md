# deploy/ — PHI-aware multi-model routing (Design C)

Deployment configurations that adapt the **model-effort-router** skill to a fixed,
compliance-constrained model lineup and wire it into two host runtimes. The design
problem and its answer are the same across both hosts; only the enforcement
primitive differs.

## The problem

Route delegated work across a model lineup where **only one provider is covered by
a HIPAA Business Associate Agreement (BAA)**, and the strongest reasoners are not:

| Role | Model | BAA? | May see PHI? |
|------|-------|------|--------------|
| Orchestrator / frontier | GLM-5.2 (Z.AI) | No | **No** |
| Deep worker | DeepSeek V4 Pro | No | **No** |
| Light/standard worker | DeepSeek V4 Flash | No | **No** |
| PHI lane — light | Gemini 2.5 Flash (Vertex) | Yes | Yes |
| PHI lane — deep | Gemini 2.5 Pro (Vertex) | Yes | Yes |

Any exposure of PHI to a non-BAA model is a reportable breach. So routing has **two
independent axes**: *effort* (cheap → capable) and *sensitivity* (PHI → BAA-only).
The base skill routes effort; these deployments add the sensitivity axis.

## The answer: Design C

Three council seats (first-principles, systems-security, HIPAA-compliance)
converged on one architecture, and challenging it produced the final shape:

1. **A deterministic gate is the trust boundary — not an LLM.** The load-bearing
   control on every crossing toward a non-BAA model is a Google Cloud DLP / Healthcare
   API de-identification pass, inside the BAA. It **fails closed**: any finding, any
   low-confidence span, any detector error → the payload stays in the BAA lane; only
   an explicit clean verdict lets text reach GLM/DeepSeek. Putting a probabilistic LLM
   in the breach-critical seat is what the design explicitly rejects. Reference
   implementation with tests: [`phi-gate/`](./phi-gate).
2. **The PHI lane has its own two tiers, both BAA.** Gemini 2.5 Flash for cheap PHI
   work, Gemini 2.5 Pro for deep PHI reasoning — so "the PHI model is a weak reasoner"
   is never a reason to move PHI toward GLM. The strong model for PHI is Pro on Vertex.
3. **Cleared, non-PHI work runs the full effort ladder** on GLM-5.2 + DeepSeek V4,
   exactly as the base skill intends.
4. **The skill's in-model confidentiality rules are the backstop behind the gate,
   never the control itself.**

The honest caveat, flagged by every seat: deterministic DLP recall on **free-text
clinical narrative** (misspellings, novel identifiers, contextual PHI) is below 100%.
The design lives on that number — keep the gate tuned toward over-routing, measure
narrative recall on production traffic, and back it with Expert Determination. Until
the gate is deployed and measured, the setup is *staging*, not an OCR-defensible
control.

## The two hosts

| | [`openclaw/`](./openclaw) | [`hermes/`](./hermes) |
|---|---|---|
| Model routing | Per-agent models + `sessions_spawn` | One global brain + one delegate model |
| Effort tiers | 4 distinct agents (T1–T4) | 2 levels: Flash delegate, GLM brain |
| PHI lane | `phi` (Flash) + `phi-deep` (Pro) agents, own ingress binding | Separate Hermes instance: Pro brain + Flash delegates |
| Gate placement | Channel/session boundary, before `sessions_spawn` | Mandatory ingress middleware in front of the brain |
| Best for | **PHI-adjacent work** — structural isolation, native Vertex, real tiers | **Non-confidential work** — brain-plans/delegate-executes |

**Recommended split:** OpenClaw owns the PHI/Vertex lane and the full effort ladder;
Hermes handles non-confidential work with its brain+delegate economics. Either host's
PHI lane can be the single Vertex lane the other defers to.

## What is verified

Every config and skill in this folder is mechanically checked:

- **`phi-gate/`** — 10 pytest cases proving the fail-closed contract (findings,
  low-confidence, detector errors, self-contradiction all route to the PHI lane;
  tokenize-only-on-clear; payload-free audit log; tool-output crossings covered).
  Run: `python3 -m pytest deploy/phi-gate/test_phi_gate.py -v`
- **OpenClaw** — `openclaw.json5` parses; invariants hold (orchestrator cannot spawn
  either PHI agent; PHI agents spawn only within the lane; PHI ingress binding first).
  Routing quiz: 21/21 including PHI-gate and Flash→Pro escalation cases.
- **Hermes** — both `config.yaml` files parse; PHI instance is Pro brain + Flash
  delegates with no non-BAA fallback. Routing quiz: 19/19.
- Each subfolder's `DEPLOY*.md` carries the exact install + verification commands and
  the deploy-time obligations (BAA confirmation, credential isolation, the DLP gate as
  net-new infrastructure).

This folder does not modify the published skill (`skills/model-effort-router/`), is
excluded from the npm package, and passes the repo's `validate.mjs` and CI unchanged.
