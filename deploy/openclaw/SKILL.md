---
name: model-effort-router
description: Use when spawning agents, delegating any task, choosing a model or effort level for a subagent or verification pass, deciding whether work needs a bigger model or more reasoning effort, orchestrating a multi-step delegated build (checkpoint verification), routing anything that touches confidential or PHI data, or when the available model lineup changes (a model is added, renamed, updated, or removed).
---

# Model Effort Router — OpenClaw / GLM-5.2 deployment

Route work by **effort required**, not by habit — and route **confidential data
by sensitivity first, before anything else**. The model running the main
conversation (the orchestrator) is GLM-5.2; everything you *delegate* (spawned
sub-agents, verification passes, background tasks) goes through this router.
Default down. Escalate only on evidence. **Sensitivity overrides everything.**

## 0. Confidentiality gate — decide this BEFORE the tier

This is a hard override and it runs first, ahead of every effort-tier decision
below. It exists because the effort tiers (GLM, DeepSeek) run on providers that
are **not covered by a HIPAA Business Associate Agreement**; only the PHI lane
is.

- **Does the task, its inputs, or its expected outputs contain PHI or otherwise
  confidential data?** (patient identifiers, clinical detail, anything a
  reasonable person would treat as protected or confidential.) If **yes** — or
  if you are not sure — the task is **CONFIDENTIAL**.
- **CONFIDENTIAL → route to the PHI lane only:** the Vertex agents — `phi`
  (**Gemini 2.5 Flash**, cheap PHI work) and `phi-deep` (**Gemini 2.5 Pro**, deep
  PHI reasoning) — the only providers here under a signed BAA. Confidential work is
  **forbidden** from the GLM and DeepSeek tiers, at any effort, for any reason —
  including "just a quick lookup" and including verification passes. A confidential
  task and every sub-task it spawns stay on the PHI lane.
- **NON-CONFIDENTIAL → route by effort tier** (section 1 onward) across the GLM
  and DeepSeek tiers as normal.
- **The PHI lane has its own two-tier ladder.** Light/standard confidential work →
  `phi` (Flash); deep confidential reasoning (unknown-cause debugging, synthesis,
  judgment-heavy analysis) → `phi-deep` (Pro). Escalation within confidential work
  is Flash → Pro, then the effort dial — the same evidence discipline as the main
  ladder, entirely inside the BAA boundary. Weak reasoning is therefore **never** a
  reason to move PHI off-lane: the strong model for PHI is Pro, not GLM. Never
  escalate a confidential task *off* the lane; a blocked-but-compliant report beats
  a disclosure.
- **The lane's entry control is deterministic, not conversational.** Where deployed,
  a DLP-based gate (see DEPLOY.md "Design C" and `deploy/phi-gate/`) inspects
  traffic at the boundary and fails closed — anything flagged or uncertain stays in
  the BAA lane, and only cleared or de-identified text may cross to GLM/DeepSeek.
  This skill's rules are the *backstop* behind that control, not a substitute for
  it: an LLM's own judgment is never the load-bearing breach boundary.
- **Splitting is allowed only when it is provably clean.** If a mixed task has a
  part that touches no confidential data (e.g. "look up the config path"), that
  part may route to the effort tiers — but only when the split is unambiguous and
  no PHI crosses into the non-PHI part. When in doubt, the whole task is
  CONFIDENTIAL.
- **Ingress: PHI must never enter through the orchestrator.** The orchestrator
  runs on GLM-5.2, which is *not* BAA-covered. If confidential data is pasted
  into the general orchestrator channel, the disclosure to the non-BAA provider
  has already happened before any routing decision could be made — classifying
  then re-routing is too late. Confidential material must therefore enter through
  the **PHI-dedicated channel**, which binds directly to the `phi` (Vertex) agent
  with no GLM hop. If PHI does appear in the orchestrator despite this, do **not**
  process or delegate it (delegation cannot un-disclose it): stop, tell the user
  it must be resent through the PHI channel, and flag the exposure.
- **Return path: confidential output stays on the lane.** A confidential task is
  answered *from* the `phi` lane and its output is delivered to the user on the
  PHI channel. Its results (summaries, extracted facts, verbatim findings,
  checkpoint artifacts) must never be returned up into the GLM orchestrator's
  context — that is a disclosure on every *successful* task, not just a misroute.
- **Structural backstop (what the config actually enforces).** Isolation here is
  three mechanisms, not credential scoping: (1) each lane is a separate agent with
  its model pinned, (2) the `phi` agent's `subagents.allowAgents` is restricted to
  itself so it cannot hand PHI down to a GLM/DeepSeek agent, and (3) PHI ingress
  is a separate binding. OpenClaw runs one process, so provider credentials are
  shared across agents unless the PHI lane is run as its **own OpenClaw instance**
  (recommended for real PHI — see DEPLOY.md). Policy and config enforce the rule
  together; keep all of it.

## 1. Tier table (non-confidential work)

Tiers are stable capability bands. Only the "current alias" column ever changes.

| Tier | Band | Spawn agent (→ model) | Route here |
|------|------|-----------------------|------------|
| **T1 — LIGHT** | fastest / cheapest available | `t1-light` → `deepseek/deepseek-v4-flash` (low effort) | lookups, file/code search, summaries, log reading, renames, formatting, simple doc edits, small verification passes |
| **T2 — STANDARD** | mid generalist | `t2-standard` → `deepseek/deepseek-v4-flash` (medium effort) | routine implementation, writing tests, single-module changes, standard refactors, README/API docs, standard verification |
| **T3 — DEEP** | strongest routinely-delegated | `t3-deep` → `deepseek/deepseek-v4-pro` | architecture, debugging with unknown cause, security review, multi-file refactors, planning, design synthesis, large/security verification |
| **T4 — FRONTIER** | top model available | `orchestrator` → `zai/glm-5.2` | only when a T3 attempt demonstrably failed, the user explicitly asks for maximum capability, or the user has authorized **taste-phase routing**: art direction, design systems, hero pages, and design/architecture docs go to a T4-pinned design agent, and execution of the resulting spec returns to T3 |

T1 and T2 run the same model (`deepseek-v4-flash`) but are **separate agents** so
the effort distinction is structural, not just advisory: `t1-light` pins
`thinkingDefault: low`, `t2-standard` pins `medium`. (OpenClaw's per-agent
`thinkingDefault` is static; splitting the agents is what makes T2 actually run
deeper than T1.) GLM-5.2 is both the orchestrator and the T4 ceiling — the top of
the non-confidential ladder.

## The effort dial (the half-step between tiers)

Tier buys capability; reasoning effort buys depth at the same tier. Where the
environment exposes an effort control (a per-agent `thinkingDefault` /
reasoning level, a session effort setting), route it with the same discipline as
the table: low for mechanical work (lookups, extraction, formatting), medium for
routine implementation, high only for judgment-heavy work (unknown-cause
debugging, security review, design synthesis). No effort control exposed →
the dial is inert; route by tier alone.

- **Raise effort before tier.** When a capability failure reads as shallow
  reasoning (missed a case, botched a judgment call) rather than missing
  capability, the sharpened same-tier retry runs at higher effort — the
  half-step that often saves a whole tier jump. It is still a work attempt
  and spends the same budget.
- **At the ceiling, effort is the whole ladder.** At the highest permitted tier —
  T4 on the main ladder, `phi-deep` (Pro) on the PHI lane — a higher effort dial
  is the only escalation left — same evidence standard, same budget.

## 2. Routing rules

1. **Confidentiality first (section 0), then pick the lowest tier that would
   succeed in one pass.** If you hesitate between two tiers, take the lower one —
   escalation is cheap, waste is not.
2. **Escalate on evidence, never on prestige.** The ladder: one retry at the
   same tier — sharpened with the failure evidence, which is new information,
   so the retry is never identical, and raised on the effort dial when the
   failure reads as shallow reasoning — then one tier up, carrying the
   hand-off brief. Skip the same-tier retry when the evidence already shows a clear
   misroute: jump straight to the tier the evidence indicates instead of
   walking the ladder one rung at a time — topping out at T3 (DeepSeek V4 Pro),
   because T4's escalation gate (a demonstrably failed T3 attempt, or an explicit
   user request) always holds; taste-phase routing is a pre-authorized dispatch,
   never an escalation destination. All of it inside the attempt budget below.
   State why you escalated in one line of your report to the user — that line is
   the routing record. **Escalation never crosses the confidentiality gate: a
   confidential task escalates only within the PHI lane — Flash (`phi`) → Pro
   (`phi-deep`), then the effort dial — never onto GLM/DeepSeek.**
3. **Shrink before you route.** A task scoped to its smallest correct version
   often drops a whole tier. Split mixed tasks: the search part is T1 even
   when the fix part is T3 — subject to the confidentiality split rule in
   section 0 (a split that would move PHI onto the effort tiers is not allowed).
4. **Verification is sized like work — but consequence outranks size.**
   Small → T1, standard → T2, large or security-sensitive → T3. Exception:
   anything that publishes, ships to production, or is hard to reverse gets
   at least T2 verification by an agent that didn't author it (T3 when the
   blast radius is real), no matter how small the change. A cheap author
   checked by an equally cheap reviewer is a correlated failure. A cheap
   result that will be trusted without anyone reading the source material
   is consequence-bearing too. **Verification of confidential work stays on the
   PHI lane** — a non-author verifier on Flash for small checks, Pro (`phi-deep`)
   for large or consequence-bearing ones.
5. **The main loop delegates — above the overhead line.** When the main model
   is a top-tier model (GLM-5.2 here), doing T1/T2 work inline is the same
   mistake as routing it to T4 — hand it down. But a subagent spawn has real
   fixed cost: if explaining the task takes more effort than doing it
   (one-liners, single lookups you can make directly), do it inline. Delegation
   pays for real work, not micro-tasks. **Exception: the GLM-5.2 orchestrator
   never does confidential work at all — not inline, and not by delegating to
   `phi` (delegation from the orchestrator means GLM already ingested the PHI).
   Confidential work originates on the PHI channel/`phi` lane; see section 0.**

## Upward escalation — the main loop can't promote itself

The router routes delegated work downward; it cannot raise the tier or
effort of the model running the main conversation. Only the user can. When
main-loop work itself — not a delegable subtask — exceeds the current tier
or effort:

- **Countable trigger:** two failed attempts at the same step, or you are
  guessing where the task demands certainty. No third attempt at the same
  tier and effort.
- **Ask in one line, then pause that step until answered** (other steps
  continue):
  `ESCALATE [effort|model] to <target>: tried <what> 2x, fails because
  <why>, expect <what the upgrade fixes>.`
  Asking while continuing to grind is the double spend; the pause is the
  point.
- **Step back down at boundaries.** Past the hard part, recommend dropping
  tier or effort at the next task boundary; never churn mid-task.

## Adaptation protocol (models change; this skill doesn't)

- The **live source of truth** for what exists is the set of model refs /
  agent IDs the OpenClaw environment actually accepts (the `agents.list` model
  fields and the providers in `models.providers`) — never a memorized list.
- **New model appears** → place it in a band by its positioning: marketed as
  fast/cheap → T1; balanced generalist → T2; most capable broadly available →
  T3; flagship above that → T4. Prefer the newer generation when a band has
  two candidates. If the name is new and its positioning is unknown, default
  it to T2 and let its first results move it up or down — placement by
  observation beats guessing. **A new model may only enter the PHI lane if it is
  covered by the BAA; positioning is irrelevant to that decision.**
- **Model removed** → collapse to the nearest existing neighbor: T1 gone →
  use T2; T2 gone → T1 for its light end, T3 for the rest; T3 gone → T2 for
  routine deep work, T4 for genuinely hard work; T4 gone → T3 is the ceiling.
  If the neighbor is gone too, keep collapsing until you land on a model that
  exists. **If the PHI lane's model is removed, confidential work is BLOCKED,
  not collapsed onto GLM/DeepSeek — report blocked and stop.**
- **Model renamed/updated** → follow the alias; bands and rules are untouched.
- **Only one model available** → every tier maps to it. The rest of the skill
  still governs: scoping, the attempt budget, hand-off briefs, and non-author
  verification are about discipline, not price — they apply unchanged. (This is
  permanently the PHI lane's situation.)
- **Alias rejected at spawn time** → treat it as removed: fall back toward
  the nearest existing tier in the same call, trying each distinct alias at
  most once per task, keep the task moving, and correct the table afterward.
  Never stall a task on a table fix. **On the PHI lane, fallback exists only
  inside the lane: a rejected Flash alias may fall to Pro (both Vertex/BAA); if
  both Vertex aliases are rejected, the confidential task is blocked — never
  failed over to GLM/DeepSeek.**
- **No delegatable models at all** → the router is inert: do the work
  inline, keep the execution discipline and attempt budget, and say so in
  the report. **Confidential work is never done inline off the PHI lane — if the
  lane is unavailable, it is blocked.**
- **Maintenance** is one edit: update the "current alias" column above and the
  matching `model` fields in `openclaw.json`. If the table and the environment
  disagree, the environment wins and the table should be corrected in the same
  session. If this skill was installed from a package (npm/git), make the same
  edit in your source repo — package updates overwrite the installed copy.
  After any edit, re-run the routing quiz in the README's Verification section
  before trusting the change.

## Execution discipline (applies to every routed task)

Bake these into the work itself AND into every delegated prompt. Even though the
config loads this skill into every agent, a sub-agent will not reliably apply it
to work you hand it unless the prompt states the rules, so the prompt must carry
them:

1. **Surface before you build.** State assumptions explicitly. If multiple
   interpretations exist, present them instead of silently picking one. If a
   simpler approach exists, say so and push back. If something is genuinely
   unclear, stop and name what's confusing.
2. **Smallest thing that works.** No features beyond what was asked, no
   abstractions for single-use code, no speculative flexibility, no error
   handling for impossible cases. If 200 lines could be 50, rewrite. Test:
   "would a senior engineer call this overcomplicated?"
3. **Touch only what you must.** No improving adjacent code, comments, or
   formatting. Match the existing style even when you'd choose differently.
   Remove only the orphans *your* change created; mention (don't delete)
   pre-existing dead code.
4. **Define done before starting.** Turn every task into a verifiable goal
   ("fix the bug" → "write a test that reproduces it, then make it pass") and
   include that success criterion in the delegated prompt. Iterate until
   verified, escalating per the routing rules and always inside the attempt
   budget below — "not verified yet" never overrides the budget's terminal
   state.
5. **Carry the confidentiality classification into every delegated prompt.**
   State "this task is CONFIDENTIAL — PHI lane only" or "non-confidential" in the
   prompt, so a sub-agent that can spawn further agents keeps the data on the
   right lane.

These disciplines feed the router: a task stripped to its smallest verifiable
form is cheaper to classify and usually routes lower.

## Failure taxonomy — react to the right failure

A failed delegation has exactly one of three causes. Escalating the wrong one
wastes a tier; diagnose first, then apply the matching response:

- **Harness failure** — greeting-only or empty reply, dropped prompt, spawn
  error. Not the model's fault, so never escalate the tier for it. Recovery
  order: retry once at the same tier; if it repeats, run the task through the
  spawn path once more or inline; last resort, do the work inline and say so —
  except confidential work, which is never moved inline or off the PHI lane: if a
  `phi` spawn cannot recover after its two harness retries, report the task
  **blocked** and stop. A blocked-but-compliant PHI task is a success; an
  off-lane recovery is a disclosure.
  Don't burn more than two spawns proving the harness is broken.
- **Prompt failure** — the agent did what you said, not what you meant:
  missing context, wrong scope, ambiguous goal. Fix the prompt and rerun at
  the **same tier**. Escalating a bad prompt buys a smarter model doing the
  wrong thing.
- **Capability failure** — correct prompt, honest attempt, wrong or
  incomplete result. This — and only this — advances routing rule 2's ladder
  (sharpened same-tier retry, then one tier up — or a direct jump on clear
  misroute evidence), always carrying the hand-off brief. On the PHI lane,
  capability escalation is Flash → Pro, then the effort dial — never off-lane.

A permission denial or policy block is none of these: adjust the approach or
do it inline (non-confidential only); retrying the identical call verbatim is
guaranteed waste. A verifier's rejection is evidence about the work attempt —
classify it with this same taxonomy and respond accordingly.

## Attempt budget — no loops, ever

Every routed task carries a hard budget; when it's spent, the task terminates
in a report, not another spawn:

1. **At most 2 work attempts per tier, 6 work spawns total per task** across
   the whole escalation chain. (Harness-failure retries have their own cap
   of 2 and don't count; neither do verification passes — see rule 4.) When
   the remaining budget can't cover both a retry and an escalation,
   escalate: reaching the right tier beats retrying the wrong one.
2. **Never resend an identical prompt after a work failure.** Every retry
   changes at least one of: scope, prompt, approach, tier — the failure
   evidence alone is a prompt change. Same input, same failure — guaranteed
   waste. (A harness failure is different: the prompt was never processed,
   so the taxonomy's single same-prompt retry is allowed.)
3. **The same failure twice means wrong diagnosis, not insufficient model.**
   Stop escalating; re-scope, split, or re-read the evidence instead.
   Re-scoping or splitting creates new tasks with fresh budgets — **once per
   original task**. If the re-scoped version also burns its budget, go to the
   terminal state, never to another re-scope.
4. **Verification has its own cap: 2 verify → fix → re-verify cycles.**
   Verifier spawns don't count as work spawns. A rejection is classified by
   the failure taxonomy; after the second rejection, escalate the author
   within the remaining budget or go to the terminal state. An escalated
   author gets one fresh verification cap — once; if that is spent too, the
   task goes to the terminal state. Consequence-bearing work that cannot
   pass verification is reported as blocked, never shipped unverified.
5. **Terminal state.** When the ceiling tier fails or the budget is spent,
   STOP and report: what was tried at which tiers, what is now known, the
   exact blocker, and the smallest step that would unblock it. A precise
   "blocked because X" report is a successful outcome; a loop never is.

## Checkpoint verification — audit the build, not just the pieces

Routing rule 4 verifies each delegation. On multi-step work the
orchestration itself needs auditing too, because every hand-off brief is a
compression and drift compounds silently across steps. The method:

1. **Anchor the spec before the first spawn.** Capture the original
   specification — the user's actual words or the requirements artifact,
   verbatim — plus the pass/fail done-criteria from execution discipline 4.
   Every later check runs against this anchor, never against an
   intermediate summary: summaries are where drift hides.
2. **Countable triggers:** after every 3 completed delegations, after any
   escalation, after any re-scope, and always before reporting done.
   Single-delegation tasks are exempt — their per-task verification IS the
   checkpoint; a second layer pays twice for the same assurance.
3. **Fresh context is the point.** The checkpoint verifier is a sub-agent
   with no prior involvement in the task, handed the spec anchor plus the
   artifacts (paths, diffs, command outputs) — never the transcript, never
   your summary of the spec. Sized by routing rule 4: consequence outranks
   size. A confidential build's checkpoint verifier is on the PHI lane.
4. **Findings travel verbatim** — failures, gaps, and unverified claims
   included — then get classified by the failure taxonomy and fixed within
   the existing caps. "It should work" is a draft, not a result.
5. **Bounded like everything else.** One verifier spawn per trigger,
   counted under the verification cap (attempt budget rule 4: 2 verify →
   fix → re-verify cycles); fixes spend the normal work budget. A
   checkpoint that still fails after its cycles follows the standard path:
   escalate the author within budget, or terminal state — reported blocked,
   never shipped unverified.

## Cooperation protocol — the cell rule

Agents are organelles, not soloists: each does one job cheaply and passes
usable material to the next. The system's output depends on the hand-offs.

1. **Scouts feed workers.** T1 gathers the context (file locations, log
   extracts, signatures, repro commands) so higher tiers spend their tokens
   only on the hard core, never on discovery a cheap model could do. (For
   confidential work, the "scout" is also on the PHI lane.)
2. **Every hand-off carries a brief, not a transcript**: the goal, what is
   done, what failed and why (exact errors, verbatim), the one question
   that remains, and the confidentiality classification. Escalating without
   the failure evidence pays for the same discovery twice.
3. **Every agent returns material, not narrative**: paths, diffs, failing
   commands, extracted facts — whatever the next agent can act on directly.
4. **The verifier is never the author** (sized by routing rule 4). Fresh eyes
   are the point; a self-reviewing agent is a correlated failure.
5. **Parallel agents get disjoint scopes.** Overlap buys the same tokens
   twice and merges into conflicts. Split by file, module, or question —
   never by "everyone look at everything."

## Delegated-prompt template

Every sub-agent prompt should contain: the task, the confidentiality
classification (CONFIDENTIAL/PHI-lane-only or non-confidential), the success
criterion, the scope limit ("touch only X; do not refactor or reformat anything
else"), and what to return (material, not narrative). On escalation or hand-off,
add the brief from cooperation rule 2. If the sub-agent can itself spawn agents,
the prompt must also carry the attempt budget, the terminal state, the
confidentiality classification, and this propagation requirement itself — so the
budget and the lane travel with every further spawn, at any depth. Do not assume
a sub-agent will apply these rules on its own, and "iterate until verified"
without a budget is a license to loop. Choose the `agentId` / model from the tier table (or the `phi`
agent for confidential work) and the effort dial where the environment takes one.
On multi-step tasks, name in each delegated prompt which of the spec anchor's
done-criteria it serves, so checkpoint verifiers can trace every artifact
back to the spec.

## Quick examples

- "Find where the config is loaded" (non-confidential) → T1 (`deepseek-v4-flash`, low effort).
- "Add a flag to the video encoder + a test" → T2 (`deepseek-v4-flash`, medium effort).
- "The cron run produces a corrupt file sometimes, cause unknown" → T3 (`deepseek-v4-pro`).
- "T3 produced two failed root-cause attempts" → T4 (`glm-5.2`), citing both failures and handing it both attempts' evidence.
- "T4 failed too" → terminal state: stop and report the blocker; no more spawns.
- "Summarize this patient's chart and flag abnormal labs" → CONFIDENTIAL → PHI lane (`phi`, Gemini 2.5 Flash), never GLM/DeepSeek, even though summarizing is normally T1.
- "Unknown-cause analysis across three patients' longitudinal records" → CONFIDENTIAL and judgment-heavy → `phi-deep` (Gemini 2.5 Pro): deep reasoning stays inside the BAA boundary.
- "Look up the config path, then de-identify and summarize this clinical note" → split only if clean: the path lookup is T1; the clinical-note step is CONFIDENTIAL and stays on the PHI lane. If any PHI would cross into the lookup, the whole task is CONFIDENTIAL.
- "Agent failed because the prompt omitted the target directory" → prompt failure: fix the prompt, same tier, no escalation.
- "T2 missed an edge case on a judgment-heavy task" → sharpened retry at T2 with a higher effort dial — the half-step before T3.
- "Third delegation of a build just completed" → checkpoint: a fresh-context verifier gets the spec anchor + artifacts before delegation four.
- "My own main-loop analysis failed twice at this tier" → one `ESCALATE` line to the user, pause that step; no third grind.
