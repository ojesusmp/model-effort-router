# model-effort-router → OpenClaw (GLM-5.2 orchestrator + DeepSeek V4 + Gemini/Vertex PHI lane)

This folder adapts the model-effort-router skill to a specific lineup and wires
it into OpenClaw. Three files:

- `SKILL.md` — the router skill, re-aliased to this lineup, plus a new
  **confidentiality gate** (section 0) that pins PHI/confidential work to the
  Gemini/Vertex lane and forbids it from GLM/DeepSeek.
- `openclaw.json5` — the OpenClaw config: providers + four agents (orchestrator,
  two DeepSeek effort tiers, one isolated PHI agent) + a default binding.
- `routing-quiz.txt` — mechanical verification, including PHI-gate cases.

## Why OpenClaw over Hermes for this

Both can host multiple providers. OpenClaw wins on the requirement that matters
most here — **PHI isolation** — because it models each lane as a separate *agent*
with its own workspace, its own model pin, and a `subagents.allowAgents` list, and
it lets you give the PHI lane its **own ingress binding**. Hermes centralizes on
one main agent with a single `delegation`/`auxiliary` model override and all
provider credentials in one process, and has no built-in Vertex provider —
isolation there is prompt-level only, which is weaker for HIPAA. OpenClaw's
`sessions_spawn` also maps cleanly onto the router's "delegate to a chosen tier"
primitive.

### The PHI data path — the part you must get right

The orchestrator runs on GLM-5.2, which is **not** BAA-covered. So PHI cannot be
routed *by* the orchestrator: classifying a message means reading it, and reading
it on GLM is already the disclosure. Two rules make this safe, and both are wired
in:

1. **Separate ingress.** PHI enters only through a dedicated channel/account whose
   binding goes straight to the `phi` (Vertex) agent — the first binding in
   `openclaw.json5`. Non-PHI traffic enters at the orchestrator. Users must be
   told: anything patient-related goes only to the confidential channel. (OpenClaw
   bindings are channel/peer-based; there is no content-based routing, which is
   exactly why a separate channel is required rather than a "detect and reroute"
   rule.)
2. **Results stay on the lane.** The `phi` agent answers the user on the PHI
   channel; its output never returns into the orchestrator's context. The
   orchestrator never spawns `phi` (note it is absent from the orchestrator's
   `allowAgents`), so there is no return hop to GLM.

### Hardened PHI isolation (recommended for production PHI)

OpenClaw runs as **one process**, so `ZAI_API_KEY`, `DEEPSEEK_API_KEY`, and Google
ADC all sit in the same environment — per-agent `allowAgents` restricts *routing*,
but it does not scope *credentials*. For real PHI, run the `phi` lane as its **own
OpenClaw instance** on a separate host/container whose environment has **only**
Vertex ADC — no `ZAI_API_KEY`, no `DEEPSEEK_API_KEY`, and critically no
`GEMINI_API_KEY`/`GOOGLE_API_KEY` (either would let the process reach a non-BAA
Gemini endpoint). Point your confidential channel at that instance. The single-
process config here is correct for staging and for the routing logic; the
two-instance split is what makes the credential boundary real.

## Model IDs (confirm against your providers before go-live)

| Lane | OpenClaw model ref | Notes |
|------|--------------------|-------|
| Orchestrator / T4 | `zai/glm-5.2` | Z.AI/Zhipu. |
| T3 deep | `deepseek/deepseek-v4-pro` | formerly `deepseek-reasoner`. |
| T1/T2 | `deepseek/deepseek-v4-flash` | formerly `deepseek-chat`. |
| PHI light | `google-vertex/gemini-2.5-flash` | Vertex AI, BAA-covered. |
| PHI deep | `google-vertex/gemini-2.5-pro` | Vertex AI, BAA-covered — deep PHI reasoning so PHI never needs GLM. |

## Credentials (never inline them in the config)

```bash
# Non-PHI providers (API keys via env)
export ZAI_API_KEY=...
export DEEPSEEK_API_KEY=...

# PHI lane — Vertex uses Application Default Credentials, NOT an API key:
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-hipaa-project
export GOOGLE_CLOUD_LOCATION=us-central1
```

Vertex ADC in OpenClaw has known rough edges (several tracked issues around
`google-vertex` "No API key found" when it falls back to API-key auth instead of
ADC/Bearer). If the PHI agent errors on auth: confirm `gcloud auth
application-default print-access-token` works, that `GOOGLE_CLOUD_PROJECT`/
`_LOCATION` are exported in the same shell that launches OpenClaw, and that no
stray `GEMINI_API_KEY`/`GOOGLE_API_KEY` is set (it can shadow ADC and silently
route PHI through the non-BAA Gemini API — unset it on the PHI host).

## Install

```bash
# 1. Skill (both installed router locations pick it up)
mkdir -p ~/.claude/skills/model-effort-router
cp deploy/openclaw/SKILL.md ~/.claude/skills/model-effort-router/SKILL.md
mkdir -p ~/.openclaw/skills/model-effort-router
cp deploy/openclaw/SKILL.md ~/.openclaw/skills/model-effort-router/SKILL.md

# 2. Config (back up any existing one first)
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak 2>/dev/null || true
cp deploy/openclaw/openclaw.json5 ~/.openclaw/openclaw.json

# 3. Validate + restart
openclaw config validate
openclaw restart   # or: systemctl --user restart openclaw
```

## Verify (four gates)

1. **Config parses** — `openclaw config validate` returns clean, and
   `openclaw models` lists `zai/glm-5.2`, `deepseek/deepseek-v4-pro`,
   `deepseek/deepseek-v4-flash`, `google-vertex/gemini-2.5-flash`.

2. **Routing logic** — the mechanical quiz. Any model can grade it because it
   tests the *rules*, not a specific model:
   ```bash
   cat deploy/openclaw/SKILL.md deploy/openclaw/routing-quiz.txt | claude -p --model haiku
   ```
   Expected: (a) t1-light, (b) t2-standard, (c) t3-deep, (d) T1,
   (e) T3 gone → escalate to T4 (glm-5.2) for the hard core; keep lookups at T1,
   (f) at-least-T2 verification by a non-author, citing consequence (publishes),
   (g) inline, (h) retry once at the same tier, no escalation (harness failure),
   (i) stop — terminal state, report the blocker, no more spawns,
   (j) the hand-off brief: what T2 tried, the exact failures verbatim, the success
   criterion, (k) all tiers map to the one alias; discipline unchanged,
   (l) no — prompt failure, fix the prompt at the same tier, (m) sharpened
   same-tier retry at higher effort, (n) a checkpoint: fresh-context non-author
   verifier vs. the verbatim spec anchor before delegation four, (o) one-line
   ESCALATE to the user, pause that step.
   **PHI gate:** (p) PHI lane (Vertex Gemini) — sensitivity overrides the T1
   default, (q) PHI lane — the note contains PHI, a lookup does not exempt it,
   (r) PHI lane — unsure defaults to CONFIDENTIAL, (s) no — never off-lane; the
   escalation available is Flash → Pro (`phi-deep`) inside the BAA boundary, then
   the effort dial, (t) blocked — do NOT fall back to DeepSeek; with both Vertex
   aliases rejected, report blocked and stop.
   **Ceiling:** (u) no — direct jumps top out at T3; T4 needs a demonstrably
   failed T3 attempt or an explicit user request.

3. **Credential hygiene on the PHI host** — confirm no non-BAA Gemini key can
   shadow ADC:
   ```bash
   env | grep -Ei 'GEMINI_API_KEY|GOOGLE_API_KEY' && echo "UNSET THESE ON THE PHI HOST" || echo "clean"
   gcloud auth application-default print-access-token >/dev/null && echo "ADC ok"
   ```

4. **Live routing** (needs your keys on the host) — send a benign non-PHI task to
   the general channel and confirm it lands on a DeepSeek/GLM agent; send a task
   to the **confidential channel** and confirm it lands on `phi` and is answered
   from that lane, and that no GLM/DeepSeek agent ever receives it. Watch
   `openclaw logs` for the spawned `agentId` per task.

## Design C: the deterministic PHI gate (the load-bearing control)

The channel split above routes traffic; it does not *inspect* it. The load-bearing
control for the GLM/DeepSeek boundary is a **deterministic DLP gate** — net-new
infrastructure you must stand up, not an OpenClaw config option. A reference
implementation of its decision logic, with tests, is in `deploy/phi-gate/`.

What it is: a small service in front of the orchestrator (and on every boundary
crossing toward a non-BAA model) that runs **Google Cloud DLP** inspection inside
your BAA:

- **Fail closed.** Any finding, any low-confidence span, any detector error or
  timeout → the payload is treated as PHI and stays in the Vertex lane. Only an
  explicit clean verdict lets text cross to GLM/DeepSeek. A miss becomes extra
  Vertex cost, never a breach.
- **Reversible tokenization, not just redaction.** Use DLP de-identification with
  deterministic/format-preserving encryption so identifiers become tokens before
  crossing to GLM/DeepSeek, and are re-identified *inside* the BAA boundary on the
  way back. Redact-only breaks workflows that need the identifiers in the answer —
  and broken workflows are what push users to bypass gates.
- **Gate every crossing, not just ingress.** PHI can enter mid-task through tool
  output (a file read, a search result). Scan payloads at each hand-off toward a
  non-BAA agent, not only the user's first message.
- **Audit log.** Every decision (clean/PHI/error, info-types found, route taken)
  goes to an append-only log — that log plus DLP's measured recall is what you show
  a regulator. Back the recall figure with Expert Determination and re-test it on
  production traffic; the number that matters is recall on free-text narrative,
  not on structured identifiers.

The skill's in-model confidentiality rules remain the backstop *behind* this gate.
Until the gate is deployed and measured, treat the setup as staging: the channel
split + skill rules reduce risk but are not, alone, an OCR-defensible control.

## Maintenance

When the lineup changes, edit two places in lockstep: the "current alias" column
in `SKILL.md` and the matching `model` fields in `openclaw.json5`, then re-run
gate 2. The PHI lane's model may only change to another BAA-covered model — never
to GLM or DeepSeek.
