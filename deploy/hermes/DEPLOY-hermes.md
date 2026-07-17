# model-effort-router → Hermes Agent (GLM-5.2 brain + DeepSeek V4 Flash delegates)

Adapts the router to Hermes, where **the brain plans and delegates and all
sub-agents run on one configured model**. Files:

- `SKILL.md` — the router, rewritten for Hermes's single-delegate-model reality
  plus a confidentiality gate.
- `config.yaml` — the general (non-confidential) instance: GLM-5.2 brain,
  DeepSeek V4 Flash delegate.
- `config.phi.yaml` — a **separate** instance whose main model is Gemini 2.5 Flash
  on Vertex, for confidential work only.
- `routing-quiz.txt` — mechanical verification, including PHI-gate cases.

## How Hermes differs from the OpenClaw deployment (read first)

Hermes uses **one** global `delegation.model`. `delegate_task` has **no per-task
model/provider/effort parameter** — it's an open, unshipped feature request
([#3719](https://github.com/NousResearch/hermes-agent/issues/3719),
[#5012](https://github.com/NousResearch/hermes-agent/issues/5012),
[#15789](https://github.com/NousResearch/hermes-agent/issues/15789),
[#34764](https://github.com/NousResearch/hermes-agent/issues/34764)), and one
report that overrides are silently ignored
([#49332](https://github.com/NousResearch/hermes-agent/issues/49332)). So:

- The four model tiers collapse to **two levels**: delegate (DeepSeek V4 Flash)
  and brain (GLM-5.2, you). "Escalation" means pulling a task **up to the brain** —
  there is no built-in escalation to a stronger model, so the brain doing it
  itself *is* the mechanism.
- **DeepSeek V4 Pro has no per-task home.** Using it means changing the global
  delegate (everything becomes Pro). DEEP work is done at the brain level instead.
- Sub-agents start with **zero context** ("they know absolutely nothing about your
  conversation"), so the `goal`/`context` brief in every `delegate_task` is
  load-bearing, not polish. SKILL.md section 3 makes this a hard rule.

## Nested delegation (max_spawn_depth: 2)

`config.yaml` sets `delegation.max_spawn_depth: 2` and `orchestrator_enabled: true`,
so the brain can spawn an **orchestrator** sub-agent that fans out its own leaf
workers (the CEO → VP → workers pattern), instead of only flat `leaf` workers.
Set it back to `1` to force flat delegation.

The trade-off, honestly: nesting gives you a cleaner brain context (only the
orchestrator's synthesis returns, not every leaf's) and local coordination of a
decomposable chunk — but it costs more (a whole subtree burns tokens), adds a
coordination layer that slows things down, and introduces the "orchestrator goes
off the rails and wastes a subtree" failure mode. Two things to hold onto:

- The orchestrator runs on the **same delegate model (DeepSeek V4 Flash)** — nesting
  adds *depth*, not a stronger model. It does **not** unlock DeepSeek V4 Pro or
  per-task model routing. Genuine planning still belongs at the brain (GLM-5.2).
- The router is the guardrail: SKILL.md §3a says default to flat delegation, use an
  orchestrator only for a genuinely decomposable execution chunk, and — critically —
  propagate the attempt budget (≤ 6 work spawns for the whole task **across the
  subtree**), the terminal state, and the confidentiality class into the
  orchestrator's brief. That budget is exactly what prevents the runaway-subtree
  waste Hermes warns about. Confidential work never uses a delegation subtree (it's
  all non-BAA Flash).

## PHI on Hermes — the honest limitation

Both models in the general instance (GLM-5.2, DeepSeek V4 Flash) are **non-BAA**,
and Hermes cannot route a single task to a different model, so **one Hermes
instance cannot safely handle PHI.**

**The posture: the general Hermes instance must be architecturally incapable of
receiving PHI.** The in-brain confidentiality gate (SKILL.md section 0) is a
backstop for accidental exposure — it is *not* a technical control, because the
brain runs on GLM and has already read any message by the time it can classify it,
and incidental PHI inside otherwise-innocuous data (a log, a file) can reach
DeepSeek during normal delegation before any classification fires. So the real
control has to live *upstream of the model*: PHI reaches you only through a
separate boundary the user cannot bypass by pasting. Concretely:

1. **Primary: keep PHI off Hermes entirely.** Route confidential work to the Vertex
   PHI lane you already run under OpenClaw (`deploy/openclaw/`) — a separate
   endpoint/UI that never touches this instance. The Hermes gate stops confidential
   work that lands here by mistake and reports blocked; it is the seatbelt, not the
   road. Pair it with input controls where you can (a distinct PHI intake channel,
   and DLP/input filtering if available) so the general instance cannot receive PHI
   in the first place.
2. **A dedicated PHI Hermes instance** (`config.phi.yaml`) whose main model is
   Gemini 2.5 Flash on Vertex, on a separate host reachable only through a channel
   that never touches the general instance. Hermes supports Vertex **natively** —
   provider `vertex` with a top-level `vertex: {project_id, region}` block
   ([Hermes Vertex guide](https://hermes-agent.nousresearch.com/docs/guides/google-vertex)).
   Auth is OAuth2 with short-lived tokens that **Hermes auto-refreshes** — no static
   API key and no manual bearer handling. Requirements before real PHI:
   - **Use a service account** on the PHI host: `VERTEX_CREDENTIALS_PATH=/path/to/
     service-account.json` (or ADC via `gcloud auth application-default login`).
   - **Confirm the Vertex project is under your Google Cloud BAA.** Vertex
     (`*-aiplatform.googleapis.com`), not the public Gemini API.
   - **Unset `GOOGLE_API_KEY` / `GEMINI_API_KEY` on that host** — either would select
     the non-BAA public `gemini` provider instead of `vertex`.
   - Keep the general instance's keys (`GLM_API_KEY`, `DEEPSEEK_API_KEY`) **off** the
     PHI host, and the Vertex service account **off** the general host.

Because you route PHI explicitly (you declare it and send it to the PHI instance),
option 2 gives you a clean, native, BAA-covered Hermes PHI lane. Option 1 (PHI on
your OpenClaw/Vertex lane, Hermes for everything else) remains equally valid if you
prefer one Vertex lane shared by both hosts — either way, PHI never touches the
general Hermes instance.

## Credentials (in ~/.hermes/.env, never in config.yaml)

```bash
# General instance host
GLM_API_KEY=...            # Z.AI / GLM (provider: zai)
DEEPSEEK_API_KEY=...

# PHI instance host ONLY (and NOT the general host):
GOOGLE_CLOUD_PROJECT=your-hipaa-project
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_CREDENTIALS_PATH=/path/to/service-account.json   # Hermes auto-refreshes the OAuth token
# ensure GLM_API_KEY / DEEPSEEK_API_KEY / GOOGLE_API_KEY / GEMINI_API_KEY are all UNSET here
```

## Install

```bash
# Skill (Hermes reads skills from its skills dir; confirm the path on your install)
mkdir -p ~/.hermes/skills/model-effort-router
cp deploy/hermes/SKILL.md ~/.hermes/skills/model-effort-router/SKILL.md

# General instance config
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak 2>/dev/null || true
cp deploy/hermes/config.yaml ~/.hermes/config.yaml
hermes config validate
```

To make the brain-plans/delegates behavior durable, keep the operating pattern in
the brain's persona/instructions (Hermes `SOUL.md` or equivalent): "plan, delegate
execution via delegate_task to the Flash delegate, synthesize the summaries" — the
same preference you set, now backed by this skill's discipline.

## Verify (three gates)

1. **Config parses** — `hermes config validate` is clean; `hermes model` (or the
   equivalent) shows brain `zai/glm-5.2` and delegate `deepseek/deepseek-v4-flash`.

2. **Routing logic** — the mechanical quiz (any model can grade it; it tests rules):
   ```bash
   cat deploy/hermes/SKILL.md deploy/hermes/routing-quiz.txt | claude -p --model haiku
   ```
   Expected: (a) delegate (Flash) — lookup, (b) delegate (Flash) — routine,
   (c) brain — DEEP/unknown-cause, (d) delegate (Flash) — summary, (e) take it over
   at the brain level, citing both failures; that IS escalation here, (f) no —
   no per-task Pro; do it at the brain level, or change the global delegate if it
   recurs, (g) inline — micro-task, (h) retry once same brief, do NOT escalate
   (harness failure), (i) a non-author verifier at the brain level (or a fresh
   Flash delegate) — auto-publish is consequence-bearing, (j) full brief: context/
   paths/prior findings/success criterion/scope/classification — because Hermes
   sub-agents start blank, (k) no — prompt failure, fix the brief same level,
   (l) checkpoint: fresh non-author delegate vs. the verbatim spec anchor before
   the fourth, (m) terminal state — stop and report the blocker.
   **PHI:** (n) PHI lane (Vertex), never Flash — sensitivity overrides effort,
   (o) no — the note has PHI, a lookup doesn't exempt it → PHI lane, (p) GLM
   already saw it on ingress; do not delegate (don't add DeepSeek), stop, tell the
   user to use the confidential/PHI instance, flag the exposure, (q) neither —
   blocked; never fall back to Flash/brain for PHI, (r) PHI lane — unsure defaults
   to CONFIDENTIAL.
   **Nesting:** (s) only for a genuinely decomposable execution chunk (default is
   flat); the orchestrator runs on the same delegate model (DeepSeek V4 Flash), so
   keep real planning at the brain; its brief must carry the attempt budget,
   terminal state, and confidentiality classification.

3. **Live routing** (needs keys) — confirm delegated tasks land on DeepSeek V4
   Flash and DEEP tasks stay on the brain; confirm the general instance is never
   handed PHI. On the PHI instance, confirm it reaches the Vertex endpoint and that
   no `GEMINI_API_KEY` is set.

## Maintenance

Edit `config.yaml` (`model`, `delegation.model`) and re-run gate 2. The PHI
instance's model may only ever be a BAA-covered model. If per-task delegate model
override ever ships in Hermes (watch the issues above), the DEEP tier could move
to a delegated DeepSeek V4 Pro — at which point re-align the tier table with the
OpenClaw version.
