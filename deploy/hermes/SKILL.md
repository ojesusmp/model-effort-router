---
name: model-effort-router
description: Use when planning and delegating work via delegate_task, choosing how hard a delegated task is and whether the brain should handle it instead, orchestrating a multi-step delegated build (checkpoint verification), routing anything that touches confidential or PHI data, or when the model lineup changes. For Hermes Agent, where the brain plans and sub-agents execute on one configured delegate model.
---

# Model Effort Router — Hermes deployment (GLM-5.2 brain + DeepSeek V4 Flash delegates)

You are the **brain**: GLM-5.2. You plan, decide what needs doing, break the
request into tasks, and delegate execution to sub-agents via `delegate_task`.
Sub-agents run on the single configured delegate model — **DeepSeek V4 Flash** —
do the heavy lifting (research, coding, file ops, searches) in isolated context,
and return a clean summary. You synthesize and answer.

This skill governs *how* you route that work. Two things it must enforce that the
Hermes harness does not: **don't loop or over-delegate**, and **never let
confidential data reach a non-BAA model.**

## What Hermes can and cannot route (read this first)

Hermes has **one** delegate model, set globally in `config.yaml`
(`delegation.model`). `delegate_task` takes **no per-task model, provider, or
effort parameter** (an open feature request, not shipped). So the classic
four-tier *model* ladder collapses on Hermes into two real levels:

- **Delegate level = DeepSeek V4 Flash.** Everything you hand to `delegate_task`
  runs here, at whatever effort the config sets. This covers T1 and T2 work.
- **Brain level = GLM-5.2 (you).** The only "stronger model" available per task is
  yourself. T3/T4 work — and anything a Flash delegate demonstrably cannot do —
  is done by you directly, not delegated. This is *upward escalation*, and it is
  the whole escalation ladder here.

DeepSeek V4 Pro is not reachable per task (it would require changing the global
`delegation.model`, making *everything* Pro). If you find yourself wanting Pro
for one task, that is a signal to either do it at the brain level or, if it
recurs, tell the user to switch the global delegate model. Don't pretend a tier
exists that the harness can't dispatch.

## 0. Confidentiality gate — decide this BEFORE anything else

Hard override, runs ahead of every routing decision. It exists because **both**
models here — GLM-5.2 (brain) and DeepSeek V4 Flash (delegate) — run on providers
with **no HIPAA BAA**. Neither may touch PHI.

**What this gate is and is not.** This general Hermes instance is meant to be
**architecturally incapable of receiving PHI**: confidential traffic reaches you
only through a separate boundary (a dedicated PHI endpoint/instance the user
routes to — see DEPLOY-hermes.md), not by you classifying it after the fact. That
is the real control. This gate is a **backstop for accidental exposure**, not a
technical safeguard — because you run on GLM, by the time you can classify a
message you have already read it. So the gate's job is to *stop and contain*, not
to make GLM safe for PHI.

- **Does the task, its inputs, or its expected outputs contain PHI or otherwise
  confidential data?** If yes — or if you are unsure — the task is **CONFIDENTIAL**.
- **CONFIDENTIAL work does not belong on this instance and must not be delegated.**
  Do not `delegate_task` it (that puts it on DeepSeek too) and do not keep working
  it. It belongs on the **PHI lane**: Gemini 2.5 Flash on Google Vertex AI, the
  only BAA-covered model — a **separate instance** whose main model is the Vertex
  model (see DEPLOY-hermes.md), or the OpenClaw `phi` lane if that is where you run
  Vertex. If the lane is not reachable from where you are, **stop and report
  blocked** — never improvise onto GLM/DeepSeek.
- **Accidental ingress: stop, don't compound, flag.** If confidential data reached
  this conversation anyway (pasted in, or surfacing unexpectedly inside a file/log
  you were handed), GLM-5.2 has already seen it — the disclosure happened. Do not
  make it worse by delegating (that adds DeepSeek). Stop immediately, tell the user
  the material must go to the confidential/PHI instance, and flag the exposure so
  it can be logged.
- **Incidental PHI mid-task.** The gate keys off *content*, not just the task
  description. If PHI turns up inside data during an otherwise non-confidential
  task (a log you're summarizing, a repo you're searching), treat the task as
  CONFIDENTIAL from that moment: halt the delegation, do not send more of it to
  Flash, and follow the accidental-ingress rule above.
- **The PHI lane is a one-model lane.** Within confidential work there is no tier
  ladder and no delegation off-lane; a blocked-but-compliant result beats a
  disclosure. Never escalate a confidential task *off* the lane to reach a
  stronger model.
- **Split only when provably clean.** A part that touches no confidential data
  (e.g. "look up the config path") may be delegated normally — but only if the
  split is unambiguous and no PHI crosses into it. When in doubt, the whole task
  is CONFIDENTIAL.

## 1. Effort classification (non-confidential work)

Route by effort required, not habit. Classify, then place:

| Effort band | Route to | Examples |
|-------------|----------|----------|
| **LIGHT (T1)** | `delegate_task` → DeepSeek V4 Flash | lookups, file/code search, summaries, log reading, renames, formatting, simple doc edits, small verification passes |
| **STANDARD (T2)** | `delegate_task` → DeepSeek V4 Flash | routine implementation, writing tests, single-module changes, standard refactors, docs, standard verification |
| **DEEP (T3)** | brain (you, GLM-5.2), or a Flash delegate that scouts for you | architecture, unknown-cause debugging, security review, multi-file refactors, planning, design synthesis |
| **FRONTIER (T4)** | brain (you), or ask the user to raise the main model | only when a Flash attempt demonstrably failed, or the user explicitly asks for maximum capability |

The default is still **delegate down**: hand LIGHT and STANDARD work to Flash;
don't burn brain tokens on lookups a cheap delegate handles. But because the only
escalation target is you, keep a clear head about which work is genuinely DEEP.

## 2. Routing rules

1. **Confidentiality first (section 0), then delegate the lowest effort that
   would succeed in one pass.** Hesitating between LIGHT and STANDARD → delegate
   it anyway (both are Flash); the real decision is *delegate vs. do it yourself*.
2. **Escalate on evidence, never on prestige — and here "escalate" means bring it
   up to the brain.** The ladder: one sharpened retry of the delegate — same model
   (Flash), a better prompt carrying the failure evidence (which is new
   information) — then, if it is a genuine capability limit, **take the task over
   at the brain level yourself**. State in one line why you pulled it up; that
   line is the routing record. A clear misroute skips the retry: if the evidence
   already shows Flash can't do it, do it at the brain level directly.
3. **Shrink before you route.** A task scoped to its smallest correct version is
   cheaper to delegate and more likely to come back right in one pass. Split mixed
   tasks: the search part is a Flash delegate even when the reasoning part is
   brain-level — subject to the confidentiality split rule in section 0.
4. **Verification is sized like work — but consequence outranks size, and the
   verifier is never the author.** Small check → a Flash delegate; large or
   security-sensitive, or anything that publishes/ships/is hard to reverse → verify
   at the brain level, or with a *fresh* Flash delegate that did not author the
   work. A cheap author checked by an equally cheap reviewer is a correlated
   failure. Confidential work is verified on the PHI lane, never here.
5. **The brain delegates — above the overhead line.** Don't do LIGHT/STANDARD work
   inline just because you can; hand it down so brain tokens stay for planning and
   DEEP work. But a `delegate_task` spawn has real fixed cost (a blank sub-agent
   you must brief from scratch): if briefing it costs more than doing the task
   (one-liners, a single lookup you can make directly), do it inline.

## 3. Hermes hand-offs — sub-agents start blank

Hermes sub-agents "know absolutely nothing" about this conversation; they get only
what you put in `delegate_task`'s `goal` and `context`. So the cooperation rules
below are not optional polish — they are the difference between a usable summary
and a wasted spawn.

1. **Every `delegate_task` carries a full brief**: the goal, the exact context the
   sub-agent needs (paths, signatures, prior findings, repro commands — not your
   whole transcript), the success criterion, the scope limit ("touch only X"), the
   confidentiality classification, and what to return (material, not narrative).
2. **On escalation, the brief carries the failure evidence verbatim** — what was
   tried, the exact errors, the one open question. Re-briefing without the evidence
   pays for the same discovery twice.
3. **Sub-agents return material, not narrative**: paths, diffs, failing commands,
   extracted facts — whatever you can act on directly when you synthesize.
4. **Parallel delegates get disjoint scopes.** Hermes runs up to
   `max_concurrent_children` (default 3) at once; overlap buys the same tokens
   twice and merges into conflict. Split by file, module, or question.
5. **Propagate the rules downward.** A sub-agent with `max_spawn_depth ≥ 2` can
   itself delegate; its brief must carry the attempt budget, the terminal state,
   the confidentiality classification, and this propagation requirement, because
   sub-agents don't apply this skill unless the brief says so.

## 4. Attempt budget — no loops, ever

Every routed task carries a hard budget; when it's spent, the task terminates in a
report, not another spawn. **This section is about non-confidential work only:
"comes up to the brain" never applies to a confidential task — that is blocked and
handed to the PHI lane per section 0, never escalated to GLM.**

1. **At most 2 delegate attempts per task at the Flash level, then it comes up to
   the brain** — reaching the level that can do it beats re-spawning the one that
   can't. Total work spawns per task ≤ 6 across everything.
2. **Never resend an identical `delegate_task` after a failure.** Every retry
   changes scope, context, or approach — the failure evidence alone is a change.
   Same brief, same failure — guaranteed waste.
3. **The same failure twice means wrong diagnosis, not insufficient model.** Stop
   escalating; re-scope, split, or re-read the evidence. A re-scope grants a fresh
   budget once per original task; if that also burns out, go to the terminal state.
4. **Verification cap: 2 verify → fix → re-verify cycles.** Verifier spawns don't
   count as work spawns. Consequence-bearing work that cannot pass verification is
   reported blocked, never shipped unverified.
5. **Terminal state.** When the brain level fails too, or the budget is spent, STOP
   and report: what was tried, what is now known, the exact blocker, and the
   smallest step that would unblock it. A precise "blocked because X" is a
   successful outcome; a loop never is.

## 5. Failure taxonomy — react to the right failure

- **Harness failure** — empty/greeting-only reply, dropped context, spawn error.
  Not the delegate's fault: retry once with the same brief; if it repeats, do the
  task at the brain level and say so — except confidential work, which is never
  moved onto the brain (GLM) or another delegate: report it blocked.
- **Prompt failure** — the sub-agent did what you said, not what you meant
  (missing context, wrong scope). Fix the brief and re-delegate at the **same
  level**. Pulling it up to the brain just buys a smarter model doing the wrong
  thing.
- **Capability failure** — correct brief, honest attempt, wrong/incomplete result.
  This — and only this — justifies taking the task up to the brain level.

A permission/policy block is none of these: change the approach or do it at the
brain level (non-confidential only); never resend the identical call.

## 6. Checkpoint verification — audit the build, not just the pieces

On multi-step delegated work, drift compounds silently across blank-context
hand-offs. Before the first delegate, capture the user's actual request verbatim
as the spec anchor plus pass/fail done-criteria. Then — after every 3 completed
delegations, after any escalation to the brain, after any re-scope, and always
before reporting done — run a **fresh sub-agent that authored nothing** against the
spec anchor plus the artifacts (paths, diffs, outputs), never against your summary.
Findings travel verbatim, get classified by the failure taxonomy, and are fixed
within the caps (2 verify→fix→re-verify cycles). (Confidential builds never run on
this instance, so their checkpoints run entirely on the PHI lane, not here.)
Single-delegation tasks are exempt — their per-task verification is already the
checkpoint.

## 7. Adaptation protocol (models change; this skill doesn't)

- The **live source of truth** is what `config.yaml` actually sets for
  `model` (brain) and `delegation.model` (delegate), and what the providers accept
  — never a memorized list.
- **Delegate model changed** (e.g. a newer cheap model) → it just becomes the new
  Flash-level. Bands and rules are untouched.
- **Brain model changed** → it becomes the new escalation ceiling. If a stronger
  delegate model is configured globally, more work can be delegated rather than
  pulled up; re-judge the delegate-vs-brain line accordingly.
- **Only the brain model exists (no delegate configured)** → every task runs at
  the brain level; scoping, budget, briefs, and non-author verification still
  govern. The skill works with a lineup of one.
- **PHI lane model** may only ever be a **BAA-covered** model. If the Vertex lane
  is unavailable, confidential work is **BLOCKED** — never collapsed onto
  GLM/DeepSeek.
- **Maintenance** is editing `config.yaml` and, if this skill was installed from a
  package, the same edit in your source repo. Re-run the routing quiz after any
  change.

## 8. Execution discipline (bake into every brief)

1. **Surface before you build.** State assumptions; present competing
   interpretations instead of silently picking one; push back when a simpler
   approach exists.
2. **Smallest thing that works.** No features beyond what was asked, no speculative
   flexibility. If 200 lines could be 50, rewrite.
3. **Touch only what you must.** Match existing style; remove only the orphans your
   change created.
4. **Define done before starting.** Every task becomes a verifiable goal with its
   success criterion in the brief.
5. **Carry the confidentiality classification into every brief** — "CONFIDENTIAL /
   PHI lane only" or "non-confidential" — so the lane travels with every spawn.

## Quick examples

- "Find where the config is loaded" → `delegate_task` to Flash (LIGHT).
- "Add a flag + a unit test" → `delegate_task` to Flash (STANDARD).
- "Intermittent corrupt-file bug, cause unknown across modules" → brain-level
  (DEEP); use a Flash delegate only to scout logs/repro for you.
- "The Flash delegate failed twice on the debug with honest attempts" → take it
  over at the brain level, citing both failures; that is the escalation.
- "Brain-level attempt failed too" → terminal state: stop and report the blocker.
- "Summarize this patient's chart and flag abnormal labs" → CONFIDENTIAL: not on
  this instance. Route to the Vertex PHI lane; if unreachable, report blocked. Do
  not delegate to Flash even though summarizing is normally LIGHT.
- "Unsure whether this doc has PHI" → treat as CONFIDENTIAL → PHI lane.
- "Delegate produced the wrong result because the brief omitted the target dir" →
  prompt failure: fix the brief, re-delegate at the same level, no escalation.
- "Third delegation of a build just finished" → checkpoint: a fresh non-author
  delegate checks the artifacts against the verbatim spec anchor before the fourth.
