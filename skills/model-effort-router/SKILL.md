---
name: model-effort-router
description: Use when spawning agents, delegating any task, choosing a model or effort level for a subagent or verification pass, deciding whether work needs a bigger model or more reasoning effort, orchestrating a multi-step delegated build (checkpoint verification), or when the available model lineup changes (a model is added, renamed, updated, or removed).
---

# Model Effort Router

Route work by **effort required**, not by habit. The model running the main
conversation is the user's choice; everything you *delegate* (Agent tool,
subagents, verification passes, background tasks) goes through this router.
Default down. Escalate only on evidence.

## Tier table

Tiers are stable capability bands. Only the "current alias" column ever changes.

| Tier | Band | Current alias | Route here |
|------|------|---------------|------------|
| **T1 — LIGHT** | fastest / cheapest available | `haiku` | lookups, file/code search, summaries, log reading, renames, formatting, simple doc edits, small verification passes |
| **T2 — STANDARD** | mid generalist | `sonnet` | routine implementation, writing tests, single-module changes, standard refactors, README/API docs, standard verification |
| **T3 — DEEP** | strongest routinely-delegated | `opus` | architecture, debugging with unknown cause, security review, multi-file refactors, planning, design synthesis, large/security verification |
| **T4 — FRONTIER** | top model available | `fable` | only when a T3 attempt demonstrably failed, or the user explicitly asks for maximum capability |

## The effort dial (the half-step between tiers)

Tier buys capability; reasoning effort buys depth at the same tier. Where the
environment exposes an effort control (a per-agent `effort` parameter, a
session effort setting), route it with the same discipline as the table:
low for mechanical work (lookups, extraction, formatting), medium for
routine implementation, high only for judgment-heavy work (unknown-cause
debugging, security review, design synthesis). No effort control exposed →
the dial is inert; route by tier alone.

- **Raise effort before tier.** When a capability failure reads as shallow
  reasoning (missed a case, botched a judgment call) rather than missing
  capability, the sharpened same-tier retry runs at higher effort — the
  half-step that often saves a whole tier jump. It is still a work attempt
  and spends the same budget.
- **At the ceiling, effort is the whole ladder.** On a one-model lineup, or
  at the highest permitted tier, a higher effort dial is the only
  escalation left — same evidence standard, same budget.

## Routing rules

1. **Pick the lowest tier that would succeed in one pass.** If you hesitate
   between two tiers, take the lower one — escalation is cheap, waste is not.
2. **Escalate on evidence, never on prestige.** The ladder: one retry at the
   same tier — sharpened with the failure evidence, which is new information,
   so the retry is never identical, and raised on the effort dial when the
   failure reads as shallow reasoning — then one tier up, carrying the
   hand-off brief. Skip the same-tier retry when the evidence already shows a clear
   misroute: jump straight to the tier the evidence indicates instead of
   walking the ladder one rung at a time — topping out at T3, because T4's
   gate (a demonstrably failed T3 attempt, or an explicit user request)
   always holds. All of it inside the attempt budget below. State why you escalated in one line of your report to the user —
   that line is the routing record.
3. **Shrink before you route.** A task scoped to its smallest correct version
   often drops a whole tier. Split mixed tasks: the search part is T1 even
   when the fix part is T3.
4. **Verification is sized like work — but consequence outranks size.**
   Small → T1, standard → T2, large or security-sensitive → T3. Exception:
   anything that publishes, ships to production, or is hard to reverse gets
   at least T2 verification by an agent that didn't author it (T3 when the
   blast radius is real), no matter how small the change. A cheap author
   checked by an equally cheap reviewer is a correlated failure. A cheap
   result that will be trusted without anyone reading the source material
   is consequence-bearing too.
5. **The main loop delegates — above the overhead line.** When the main model
   is a top-tier model, doing T1/T2 work inline is the same mistake as routing
   it to T4 — hand it down. But a subagent spawn has real fixed cost: if
   explaining the task takes more effort than doing it (one-liners, single
   lookups you can make directly), do it inline. Delegation pays for real
   work, not micro-tasks.

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

- The **live source of truth** for what exists is the `model` parameter the
  Agent tool accepts in the current environment — never a memorized list.
- **New model appears** → place it in a band by its positioning: marketed as
  fast/cheap → T1; balanced generalist → T2; most capable broadly available →
  T3; flagship above that → T4. Prefer the newer generation when a band has
  two candidates. If the name is new and its positioning is unknown, default
  it to T2 and let its first results move it up or down — placement by
  observation beats guessing.
- **Model removed** → collapse to the nearest existing neighbor: T1 gone →
  use T2; T2 gone → T1 for its light end, T3 for the rest; T3 gone → T2 for
  routine deep work, T4 for genuinely hard work; T4 gone → T3 is the ceiling.
  If the neighbor is gone too, keep collapsing until you land on a model that
  exists.
- **Model renamed/updated** → follow the alias; bands and rules are untouched.
- **Only one model available** → every tier maps to it. The rest of the skill
  still governs: scoping, the attempt budget, hand-off briefs, and non-author
  verification are about discipline, not price — they apply unchanged.
- **Alias rejected at spawn time** → treat it as removed: fall back toward
  the nearest existing tier in the same call, trying each distinct alias at
  most once per task, keep the task moving, and correct the table afterward.
  Never stall a task on a table fix.
- **No delegatable models at all** (the Agent tool takes no `model`
  parameter, or every alias was rejected) → the router is inert: do the work
  inline, keep the execution discipline and attempt budget, and say so in
  the report.
- **Maintenance** is one edit: update the "current alias" column above. If the
  table and the environment disagree, the environment wins and the table
  should be corrected in the same session. If this skill was installed from a
  package (npm/git), make the same edit in your source repo — package updates
  overwrite the installed copy. After any edit, re-run the routing quiz in the
  README's Verification section before trusting the change.

## Execution discipline (applies to every routed task)

Bake these into the work itself AND into every delegated prompt — subagents do
not inherit this skill, so the prompt must carry the rules:

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

These disciplines feed the router: a task stripped to its smallest verifiable
form is cheaper to classify and usually routes lower.

## Failure taxonomy — react to the right failure

A failed delegation has exactly one of three causes. Escalating the wrong one
wastes a tier; diagnose first, then apply the matching response:

- **Harness failure** — greeting-only or empty reply, dropped prompt, spawn
  error. Not the model's fault, so never escalate the tier for it. Recovery
  order: retry once at the same tier; if it repeats, run the task headless
  (`claude -p --model <alias>` with the prompt on stdin), which bypasses the
  spawn path; last resort, do the work inline and say so. Don't burn more
  than two spawns proving the harness is broken.
- **Prompt failure** — the agent did what you said, not what you meant:
  missing context, wrong scope, ambiguous goal. Fix the prompt and rerun at
  the **same tier**. Escalating a bad prompt buys a smarter model doing the
  wrong thing.
- **Capability failure** — correct prompt, honest attempt, wrong or
  incomplete result. This — and only this — advances routing rule 2's ladder
  (sharpened same-tier retry, then one tier up — or a direct jump on clear
  misroute evidence), always carrying the hand-off brief.

A permission denial or policy block is none of these: adjust the approach or
do it inline; retrying the identical call verbatim is guaranteed waste. A
verifier's rejection is evidence about the work attempt — classify it with
this same taxonomy and respond accordingly.

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
3. **Fresh context is the point.** The checkpoint verifier is a subagent
   with no prior involvement in the task, handed the spec anchor plus the
   artifacts (paths, diffs, command outputs) — never the transcript, never
   your summary of the spec. Sized by routing rule 4: consequence outranks
   size.
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
   only on the hard core, never on discovery a cheap model could do.
2. **Every hand-off carries a brief, not a transcript**: the goal, what is
   done, what failed and why (exact errors, verbatim), and the one question
   that remains. Escalating without the failure evidence pays for the same
   discovery twice.
3. **Every agent returns material, not narrative**: paths, diffs, failing
   commands, extracted facts — whatever the next agent can act on directly.
4. **The verifier is never the author** (sized by routing rule 4). Fresh eyes
   are the point; a self-reviewing agent is a correlated failure.
5. **Parallel agents get disjoint scopes.** Overlap buys the same tokens
   twice and merges into conflicts. Split by file, module, or question —
   never by "everyone look at everything."

## Delegated-prompt template

Every Agent/subagent prompt should contain: the task, the success criterion,
the scope limit ("touch only X; do not refactor or reformat anything else"),
and what to return (material, not narrative). On escalation or hand-off, add
the brief from cooperation rule 2. If the subagent can itself spawn agents,
the prompt must also carry the attempt budget, the terminal state, and this
propagation requirement itself — so the budget travels with every further
spawn, at any depth. Subagents don't inherit this skill, and "iterate until
verified" without a budget is a license to loop. Choose `model` from the
tier table and `effort` from the dial where the environment takes one. On
multi-step tasks, name in each delegated prompt which of the spec anchor's
done-criteria it serves, so checkpoint verifiers can trace every artifact
back to the spec.

## Quick examples

- "Find where the config is loaded" → T1.
- "Add a flag to the video encoder + a test" → T2.
- "The cron run produces a corrupt file sometimes, cause unknown" → T3.
- "T3 produced two failed root-cause attempts" → T4, citing both failures and
  handing it both attempts' evidence.
- "T4 failed too" → terminal state: stop and report the blocker; no more spawns.
- "Agent failed because the prompt omitted the target directory" → prompt
  failure: fix the prompt, same tier, no escalation.
- "T2 missed an edge case on a judgment-heavy task" → sharpened retry at T2
  with a higher effort dial — the half-step before T3.
- "Third delegation of a build just completed" → checkpoint: a fresh-context
  verifier gets the spec anchor + artifacts before delegation four.
- "My own main-loop analysis failed twice at this tier" → one `ESCALATE`
  line to the user, pause that step; no third grind.
