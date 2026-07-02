# model-effort-router

> The right model for every task — automatically, cheaply, and future-proof.

[![npm version](https://img.shields.io/npm/v/@ojesusmp/model-effort-router.svg)](https://www.npmjs.com/package/@ojesusmp/model-effort-router)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

**model-effort-router** is a Claude Code skill that makes the assistant match every delegated task to the *cheapest model tier that can do it well* — instead of habitually sending everything to the most expensive model. A file lookup goes to the fastest, cheapest model; routine implementation goes to the mid generalist; gnarly debugging goes to the strongest routinely-used model; and the top-tier flagship is reserved for work that demonstrably defeated everything below it.

Because the skill defines **stable capability bands** rather than hardcoded model names, it survives model launches, renames, and retirements: when the lineup changes, the router adapts by rule, and maintenance is a one-cell table edit.

It also embeds an execution discipline into every routed task — surface assumptions, build the smallest thing that works, touch only what you must, define a verifiable "done" before starting — so cheaper models stay reliable and expensive models stay scoped.

Since v1.3.0 the router is also **guaranteed to terminate** (a hard attempt budget with a defined terminal state — no retry loop, no runaway spawning, at any delegation depth) and **cooperative by design**: cheap scouts gather context for bigger workers, every escalation hands forward the failure evidence so no tier pays for the same discovery twice, and verification is always done by fresh eyes.

---

## Table of contents

- [Why this exists](#why-this-exists)
- [Install](#install)
- [How it works](#how-it-works)
  - [The tier table](#the-tier-table)
  - [Routing rules](#routing-rules)
  - [Adaptation protocol](#adaptation-protocol)
  - [Execution discipline](#execution-discipline)
  - [Failure taxonomy](#failure-taxonomy)
  - [Attempt budget](#attempt-budget)
  - [Cooperation protocol](#cooperation-protocol)
- [Usage examples](#usage-examples)
- [Making it always-on](#making-it-always-on)
- [Enforcement and measurement (optional hooks)](#enforcement-and-measurement-optional-hooks)
- [Customization](#customization)
- [Verification](#verification)
- [Limitations](#limitations)
- [Troubleshooting / FAQ](#troubleshooting--faq)
- [Contributing](#contributing)
- [Security](#security)
- [Credits](#credits)
- [License](#license)

---

## Why this exists

Orchestrating assistants have a prestige bias: when they delegate work to subagents, they tend to pick the biggest model available "to be safe." That wastes money and time on tasks a small model handles perfectly, and — worse — it removes the headroom you need when something genuinely hard shows up.

The second problem is churn. Model lineups change several times a year. Any routing rule written as "use model X for Y" silently rots the day X is renamed or retired.

This skill fixes both: effort-based routing with evidence-based escalation, expressed in tiers that outlive any individual model.

In a verification test, the same small model asked to plan delegations **without** the skill sent an unknown-cause debugging task straight to the most expensive flagship; **with** the skill it correctly routed the task one tier down and answered a "what if this model is removed tomorrow?" question exactly per the adaptation protocol.

---

## Install

Pick one. All three install the skill into your Claude Code skills directory automatically.

### 1. npm (recommended)

```bash
npm install -g @ojesusmp/model-effort-router
```

Update later with the same command.

**Verify:** check that `~/.claude/skills/model-effort-router/SKILL.md` exists (`%USERPROFILE%\.claude\skills\model-effort-router\SKILL.md` on Windows).

### 2. Git (latest unreleased code)

```bash
npm install -g github:ojesusmp/model-effort-router
```

Same postinstall, but pulls straight from the repo's `main` branch.

**Verify:** same file check as above.

### 3. Claude Code plugin marketplace

Inside Claude Code:

```
/plugin marketplace add ojesusmp/model-effort-router
/plugin install model-effort-router@model-effort-router
```

**Verify:** in a fresh conversation, ask Claude Code to "delegate a simple file search and tell me which model tier you'd route it to." It should answer with the LIGHT tier, not the flagship.

---

## How it works

### The tier table

Tiers are **stable capability bands**. Only the "current alias" column ever changes.

| Tier | Band | Current alias | Route here |
|------|------|---------------|------------|
| **T1 — LIGHT** | fastest / cheapest available | `haiku` | lookups, file/code search, summaries, log reading, renames, formatting, simple doc edits, small verification passes |
| **T2 — STANDARD** | mid generalist | `sonnet` | routine implementation, writing tests, single-module changes, standard refactors, docs, standard verification |
| **T3 — DEEP** | strongest routinely-delegated | `opus` | architecture, debugging with unknown cause, security review, multi-file refactors, planning, design synthesis, large/security verification |
| **T4 — FRONTIER** | top model available | `fable` | only when a T3 attempt demonstrably failed, or the user explicitly asks for maximum capability |

### Routing rules

1. **Pick the lowest tier that would succeed in one pass.** When hesitating between two tiers, take the lower — escalation is cheap, waste is not.
2. **Escalate on evidence, never on prestige.** The ladder: one retry at the same tier — sharpened with the failure evidence, so never identical — then one tier up, always within the [attempt budget](#attempt-budget), always carrying the [hand-off brief](#cooperation-protocol). A clear misroute skips the ladder: the task jumps straight to the tier the evidence indicates — topping out at T3, because T4's gate (a demonstrably failed T3 attempt or an explicit user request) always holds. The reason for escalating is stated in one line of the report to the user — that line is the routing record.
3. **Shrink before you route.** A task scoped to its smallest correct version often drops a whole tier. Mixed tasks get split: the search part is T1 even when the fix part is T3.
4. **Verification is sized like work — but consequence outranks size.** Small → T1, standard → T2, large or security-sensitive → T3. Exception: anything that publishes, ships to production, or is hard to reverse gets at least T2 verification by an agent that didn't author it (T3 when the blast radius is real), no matter how small the change. A cheap author checked by an equally cheap reviewer is a correlated failure.
5. **The main loop delegates — above the overhead line.** When the main conversation runs on a top-tier model, doing T1/T2 work inline is the same mistake as routing it to T4. But a subagent spawn has real fixed cost: one-liners and single lookups are done inline. Delegation pays for real work, not micro-tasks.

### Adaptation protocol

This is what keeps the skill alive across model generations:

- The **live source of truth** for what exists is the set of model aliases the environment actually accepts — never a memorized list.
- **New model appears** → it is placed in a band by its positioning: marketed as fast/cheap → T1; balanced generalist → T2; most capable broadly available → T3; flagship above that → T4. The newer generation wins when a band has two candidates. A brand-new name with unknown positioning defaults to T2, and its first results move it up or down — placement by observation, not guessing.
- **Model removed** → the band collapses to its nearest *existing* neighbor: T1 gone → T2; T2 gone → T1 for its light end, T3 for the rest; T3 gone → T2 for routine deep work, T4 for genuinely hard work; T4 gone → T3 is the ceiling. If the neighbor is gone too, collapsing continues until a model exists.
- **Model renamed or updated** → follow the alias; bands and rules are untouched.
- **Only one model available** → every tier maps to it, and the rest of the skill still governs: scoping, the attempt budget, hand-off briefs, and non-author verification are about discipline, not price. The router works with *any* Claude lineup, including a lineup of one.
- **Alias rejected at spawn time** → treated as removed: fallback toward the nearest existing tier in the same call, each distinct alias tried at most once per task, table corrected afterward. A task is never stalled on a table fix.
- **No delegatable models at all** (no `model` parameter, or every alias rejected) → the router is inert: the work is done inline with the execution discipline and attempt budget intact, and the report says so.
- **Maintenance is one edit**: update the "current alias" column in `SKILL.md`. If the table and the environment ever disagree, the environment wins.

### Execution discipline

Every routed task — and every prompt handed to a subagent, since subagents don't inherit skills — carries four rules:

1. **Surface before you build.** State assumptions explicitly; present competing interpretations instead of silently picking one; push back when a simpler approach exists.
2. **Smallest thing that works.** No features beyond what was asked, no abstractions for single-use code, no speculative flexibility.
3. **Touch only what you must.** No improving adjacent code; match the existing style; remove only the orphans your own change created.
4. **Define done before starting.** Every task becomes a verifiable goal with its success criterion included in the delegated prompt.

These disciplines feed the router: a task stripped to its smallest verifiable form is cheaper to classify and usually routes lower.

### Failure taxonomy

A failed delegation has exactly one of three causes, and each gets a different response — escalating the wrong one wastes a tier:

| Failure | Signature | Response |
|---|---|---|
| **Harness** | greeting-only / empty reply, dropped prompt, spawn error | Retry once at the same tier → headless (`claude -p`) → inline. **Never escalate the tier for this.** Max two spawns proving the harness is broken. |
| **Prompt** | the agent did what you said, not what you meant — missing context, wrong scope | Fix the prompt, rerun at the **same tier**. Escalating a bad prompt buys a smarter model doing the wrong thing. |
| **Capability** | correct prompt, honest attempt, wrong or incomplete result | This — and only this — advances routing rule 2's ladder (sharpened same-tier retry, then one tier up — or a direct jump on clear misroute evidence), carrying the hand-off brief. |

A permission denial or policy block is none of these: the approach changes or the work moves inline — the identical call is never retried verbatim. A verifier's rejection is evidence about the work attempt and is classified with this same taxonomy.

### Attempt budget

This is the anti-loop guarantee. Every routed task carries a hard budget, and when it's spent the task terminates in a report, not another spawn:

1. **At most 2 work attempts per tier, 6 work spawns total per task** across the whole escalation chain (harness-failure retries have their own cap of 2 and don't count; neither do verification passes). When the remaining budget can't cover both a retry and an escalation, the task escalates — reaching the right tier beats retrying the wrong one.
2. **An identical prompt is never resent after a work failure.** Every retry changes scope, prompt, approach, or tier — the failure evidence alone is a prompt change. (A harness failure is different: the prompt was never processed, so its single same-prompt retry is allowed.)
3. **The same failure twice means wrong diagnosis, not insufficient model** — the response is re-scoping or splitting, not escalating. A re-scope grants fresh budgets **once per original task**; if the re-scoped version also burns its budget, the task goes to the terminal state, never to another re-scope.
4. **Verification has its own cap: 2 verify → fix → re-verify cycles.** Verifier spawns don't count as work spawns; a rejection is classified by the failure taxonomy, and after the second rejection the author escalates within the remaining budget or the task goes to the terminal state. An escalated author gets one fresh verification cap — once; if that is spent too, terminal state. Consequence-bearing work that cannot pass verification is reported as blocked, never shipped unverified.
5. **Terminal state.** When the ceiling tier fails or the budget is spent, the orchestrator STOPS and reports: what was tried at which tiers, what is now known, the exact blocker, and the smallest unblocking step. A precise "blocked because X" report is a successful outcome; a loop never is.

### Cooperation protocol

Agents are organelles, not soloists — like a cell, the system's output depends on parts doing one job each and handing usable material to the next:

1. **Scouts feed workers.** T1 gathers context (file locations, log extracts, signatures, repro commands) so higher tiers spend tokens only on the hard core, never on discovery a cheap model could do.
2. **Hand-offs carry a brief, not a transcript**: the goal, what's done, what failed and why (exact errors, verbatim), and the one question that remains. Escalating without the failure evidence pays for the same discovery twice.
3. **Agents return material, not narrative**: paths, diffs, failing commands, extracted facts — whatever the next agent can act on directly.
4. **The verifier is never the author.** Fresh eyes are the point; a self-reviewing agent is a correlated failure.
5. **Parallel agents get disjoint scopes** — split by file, module, or question, never "everyone look at everything."

---

## Usage examples

| You ask Claude Code to… | The router sends it to… |
|---|---|
| "Find where the config is loaded" | T1 (LIGHT) |
| "Add a `--verbose` flag plus a unit test" | T2 (STANDARD) |
| "Sometimes the output file is corrupt, no idea why" | T3 (DEEP) |
| "T3 failed twice on this — bring the big guns" | T4 (FRONTIER), citing both failures |
| "Summarize this 200-line log" | T1 (LIGHT) |
| "Review this auth change for security issues" | T3 (DEEP — security verification) |
| "T4 failed too" | Nowhere — terminal state: stop and report the exact blocker |
| "Agent failed because my prompt omitted the target dir" | Same tier with a fixed prompt (prompt failure ≠ capability failure) |

---

## Making it always-on

The skill activates when Claude Code consults it for delegation decisions. To make it apply in **every** session without being asked, add a pointer to your global `~/.claude/CLAUDE.md`:

```markdown
# model-effort-router (ALWAYS-ON for delegation)
- **model-effort-router** (`~/.claude/skills/model-effort-router/SKILL.md`) — invoke before
  spawning agents, choosing a model for any subagent/verification pass, or when the model
  lineup changes.
```

---

## Enforcement and measurement (optional hooks)

The skill is policy; these two hooks make it harder to ignore and prove what it saves. Both go in `~/.claude/settings.json` (they need `python` on PATH).

**Enforcement** — a PreToolUse hook that flags any agent spawn with no explicit `model` parameter (which silently inherits the expensive main-loop model). It stays silent when a tier was chosen:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Agent|Task",
      "hooks": [{
        "type": "command",
        "command": "python -c \"import json,sys; d=json.load(sys.stdin); m=(d.get('tool_input') or {}).get('model'); print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','additionalContext':'[ROUTER] This agent call passes NO model parameter, so it inherits the expensive main-loop model. Pass an explicit tier unless the agent type defines its own model or T4 is deliberately justified.'}}) if not m else '')\""
      }]
    }]
  }
}
```

**Measurement** — a PostToolUse hook that appends one JSON line per delegation (UTC time, model or `inherit`, agent type, task description) to `~/.claude/router-ledger.jsonl`. That file is the evidence: after a few weeks you can see exactly how work distributes across tiers and tune the boundaries on data instead of taste:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Agent|Task",
      "hooks": [{
        "type": "command",
        "command": "python -c \"import json,sys,os,datetime; d=json.load(sys.stdin); ti=(d.get('tool_input') or {}); open(os.path.expanduser('~/.claude/router-ledger.jsonl'),'a',encoding='utf-8').write(json.dumps({'t':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'model':ti.get('model') or 'inherit','type':ti.get('subagent_type') or '','desc':(ti.get('description') or '')[:80]})+chr(10))\""
      }]
    }]
  }
}
```

Merge them into any existing `PreToolUse`/`PostToolUse` arrays rather than replacing them. The enforcement hook is deliberately soft (a visible reminder, not a block) so it can't break multi-agent workflows that legitimately omit the parameter.

### Ledger dashboard

`tools/router-dashboard.html` turns the measurement ledger into pictures: stat tiles (delegation count, explicitly-routed share, cost index vs. an all-frontier baseline, busiest tier), delegations by tier, a stacked timeline, and a full table view. Open the file in any browser and drop `~/.claude/router-ledger.jsonl` onto it — everything runs locally in the page, no network, no upload. Cost weights are editable in the filter row; entries with no explicit model are counted at the T4 weight (they inherit the main-loop model — the worst case the enforcement hook exists to prevent), and since the ledger has no token counts the cost index is a relative proxy, clearly labeled as such.

---

## Customization

- **Model lineup changed?** Edit the "Current alias" column in `SKILL.md` — nothing else. Bands, rules, and the adaptation protocol are deliberately model-agnostic. If you installed via npm or git, make the same edit in your clone of this repo too: package updates overwrite the installed copy.
- **Different tier boundaries?** Move work types between the "Route here" cells. Keep the four-band structure: it matches how model families are actually positioned (fast / balanced / deep / flagship).
- **Stricter escalation?** Change rule 2's "one retry, then one tier up" to your taste — e.g., two retries for expensive tiers.
- **House discipline?** The four execution rules are a good default; append your own (e.g., "always run the linter") in the same numbered list.

---

## Verification

Every release is verified two ways: the mechanical quiz gate below, and — for v1.3.0 — three rounds of independent adversarial audit run until a round found zero defects (round 1: eight defects found and fixed; round 2: fixes confirmed, three seam defects found and fixed; round 3: no new defects). The audit trail is in the [CHANGELOG](./CHANGELOG.md).

The skill also ships verified by a baseline/with-skill comparison ("RED/GREEN"):

- **Without the skill**, a small model planning delegations routed an unknown-cause, multi-module debugging task to the flagship tier and improvised an inconsistent answer about model removal.
- **With the skill**, the same model routed that task to T3 (DEEP), kept lookups and summaries at T1, and answered the removal question exactly per the adaptation protocol: "T3 gone → T4 only for genuinely hard work."

To re-verify after editing the skill, run the bundled quiz mechanically (any cheap model works). The quiz contains only the questions — the live SKILL.md is concatenated in front, so the test can never drift from the rules it tests:

```bash
cat SKILL.md test/routing-quiz.txt | claude -p --model haiku
```

Expected: (a) T1, (b) T2, (c) T3, (d) T1, (e) T4 with the removal reasoning, (f) at-least-T2 verification by a non-author citing consequence, (g) inline, (h) retry once at the same tier without escalating — a greeting-only reply is harness failure, not model failure, (i) stop — the ceiling tier is exhausted (2 attempts at T3 and at T4), terminal state: report what was tried and the exact blocker, no more spawns, (j) the hand-off brief: what T2 tried, the exact failures/evidence verbatim, and the success criterion, (k) all tiers map to the one alias; scoping, budget, and verification discipline unchanged, (l) no — prompt failure: fix the prompt, same tier. Any drift from those answers means your edit broke a rule.

---

## Limitations

Honesty about what this skill cannot do:

- **It's policy, not a hard guarantee.** The rules steer the orchestrating model; the enforcement hook makes violations visible at the moment they happen, but nothing physically blocks a wasteful choice. A determined rationalization can still route badly or overrun the attempt budget — the budget and terminal state make a runaway loop a *rule violation* with a defined exit, not an impossibility.
- **It can't fix the delegation harness.** If your Claude Code subagent spawns drop prompts or carry heavy fixed overhead, the skill can only respond sensibly (the harness-misbehaves recovery path: retry once, go headless, go inline). It cannot make spawning reliable.
- **It doesn't govern the main conversation.** Your chosen main-loop model is untouched — only delegated work is routed. And subagents don't inherit the skill; the orchestrator must copy the discipline into each prompt, which the skill mandates but cannot force.
- **Its judgment is bounded by the task description.** A disguised-hard task can still be under-routed. The consequence rule (including "a cheap result trusted without anyone checking the source is consequence-bearing") narrows this gap; it cannot close it completely.

---

## Troubleshooting / FAQ

**Claude still uses the big model for everything.**
Make sure the always-on pointer is in your `~/.claude/CLAUDE.md` (see [Making it always-on](#making-it-always-on)) and the skill file exists in `~/.claude/skills/model-effort-router/`.

**A model name in the table doesn't exist anymore.**
That's expected eventually — the table is a snapshot, the protocol is permanent. Update the alias column; the environment's accepted aliases always win.

**Does this change the model my main conversation runs on?**
No. The router governs *delegated* work (subagents, verification passes, background tasks). Your main-loop model stays whatever you chose.

**Why not just always use the best model?**
Cost and speed, but also quality: the discipline section keeps tasks small and verifiable, which is what actually prevents errors — tier size mostly buys depth, not care.

**Is this tied to specific Claude models?**
No. The aliases in the table are examples of the current lineup. The bands (fast/cheap, mid, deep, flagship) apply to any model family.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Bug reports and feature requests via
[GitHub Issues](https://github.com/ojesusmp/model-effort-router/issues).

## Security

See [SECURITY.md](./SECURITY.md). The skill is a single Markdown instruction file —
it executes nothing and phones home to no one.

## Credits

Created by **Orlando Molina** ([@ojesusmp](https://github.com/ojesusmp)) / TruePointAgents.

## License

[MIT](./LICENSE)
