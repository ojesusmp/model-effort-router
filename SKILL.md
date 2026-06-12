---
name: model-effort-router
description: Use when spawning agents, delegating any task, choosing a model for a subagent or verification pass, deciding whether work needs a bigger model, or when the available model lineup changes (a model is added, renamed, updated, or removed).
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

## Routing rules

1. **Pick the lowest tier that would succeed in one pass.** If you hesitate
   between two tiers, take the lower one — escalation is cheap, waste is not.
2. **Escalate on evidence, never on prestige.** One retry at the same tier
   (with a sharpened prompt), then one tier up. Log why you escalated.
3. **Shrink before you route.** A task scoped to its smallest correct version
   often drops a whole tier. Split mixed tasks: the search part is T1 even
   when the fix part is T3.
4. **Verification is sized like work**: small → T1, standard → T2,
   large or security-sensitive → T3. The verifier never needs to outrank the
   author by default.
5. **The main loop delegates.** When the main model is a top-tier model, doing
   T1/T2 work inline is the same mistake as routing it to T4 — hand it down.

## Adaptation protocol (models change; this skill doesn't)

- The **live source of truth** for what exists is the `model` parameter the
  Agent tool accepts in the current environment — never a memorized list.
- **New model appears** → place it in a band by its positioning: marketed as
  fast/cheap → T1; balanced generalist → T2; most capable broadly available →
  T3; flagship above that → T4. Prefer the newer generation when a band has
  two candidates.
- **Model removed** → collapse to the nearest neighbor: T1 gone → use T2;
  T3 gone → T2 for routine deep work, T4 for genuinely hard work; T4 gone →
  T3 is the ceiling.
- **Model renamed/updated** → follow the alias; bands and rules are untouched.
- **Maintenance** is one edit: update the "current alias" column above. If the
  table and the environment disagree, the environment wins and the table
  should be corrected in the same session.

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
   include that success criterion in the delegated prompt. Loop until
   verified, escalating per the routing rules.

These disciplines feed the router: a task stripped to its smallest verifiable
form is cheaper to classify and usually routes lower.

## Delegated-prompt template

Every Agent/subagent prompt should contain: the task, the success criterion,
the scope limit ("touch only X; do not refactor or reformat anything else"),
and what to return. Choose `model` from the tier table.

## Quick examples

- "Find where the config is loaded" → T1.
- "Add a flag to the video encoder + a test" → T2.
- "The cron run produces a corrupt file sometimes, cause unknown" → T3.
- "T3 produced two failed root-cause attempts" → T4, citing both failures.
