# model-effort-router

> The right model for every task — automatically, cheaply, and future-proof.

[![npm version](https://img.shields.io/npm/v/@ojesusmp/model-effort-router.svg)](https://www.npmjs.com/package/@ojesusmp/model-effort-router)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

**model-effort-router** is a Claude Code skill that makes the assistant match every delegated task to the *cheapest model tier that can do it well* — instead of habitually sending everything to the most expensive model. A file lookup goes to the fastest, cheapest model; routine implementation goes to the mid generalist; gnarly debugging goes to the strongest routinely-used model; and the top-tier flagship is reserved for work that demonstrably defeated everything below it.

Because the skill defines **stable capability bands** rather than hardcoded model names, it survives model launches, renames, and retirements: when the lineup changes, the router adapts by rule, and maintenance is a one-cell table edit.

It also embeds an execution discipline into every routed task — surface assumptions, build the smallest thing that works, touch only what you must, define a verifiable "done" before starting — so cheaper models stay reliable and expensive models stay scoped.

---

## Table of contents

- [Why this exists](#why-this-exists)
- [Install](#install)
- [How it works](#how-it-works)
  - [The tier table](#the-tier-table)
  - [Routing rules](#routing-rules)
  - [Adaptation protocol](#adaptation-protocol)
  - [Execution discipline](#execution-discipline)
- [Usage examples](#usage-examples)
- [Making it always-on](#making-it-always-on)
- [Customization](#customization)
- [Verification](#verification)
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
2. **Escalate on evidence, never on prestige.** One retry at the same tier with a sharpened prompt, then one tier up. The reason for escalating is stated in one line of the report to the user — that line is the routing record.
3. **Shrink before you route.** A task scoped to its smallest correct version often drops a whole tier. Mixed tasks get split: the search part is T1 even when the fix part is T3.
4. **Verification is sized like work — but consequence outranks size.** Small → T1, standard → T2, large or security-sensitive → T3. Exception: anything that publishes, ships to production, or is hard to reverse gets at least T2 verification by an agent that didn't author it (T3 when the blast radius is real), no matter how small the change. A cheap author checked by an equally cheap reviewer is a correlated failure.
5. **The main loop delegates — above the overhead line.** When the main conversation runs on a top-tier model, doing T1/T2 work inline is the same mistake as routing it to T4. But a subagent spawn has real fixed cost: one-liners and single lookups are done inline. Delegation pays for real work, not micro-tasks.

### Adaptation protocol

This is what keeps the skill alive across model generations:

- The **live source of truth** for what exists is the set of model aliases the environment actually accepts — never a memorized list.
- **New model appears** → it is placed in a band by its positioning: marketed as fast/cheap → T1; balanced generalist → T2; most capable broadly available → T3; flagship above that → T4. The newer generation wins when a band has two candidates.
- **Model removed** → the band collapses to its nearest neighbor: T1 gone → T2; T3 gone → T2 for routine deep work, T4 for genuinely hard work; T4 gone → T3 is the ceiling.
- **Model renamed or updated** → follow the alias; bands and rules are untouched.
- **Maintenance is one edit**: update the "current alias" column in `SKILL.md`. If the table and the environment ever disagree, the environment wins.

### Execution discipline

Every routed task — and every prompt handed to a subagent, since subagents don't inherit skills — carries four rules:

1. **Surface before you build.** State assumptions explicitly; present competing interpretations instead of silently picking one; push back when a simpler approach exists.
2. **Smallest thing that works.** No features beyond what was asked, no abstractions for single-use code, no speculative flexibility.
3. **Touch only what you must.** No improving adjacent code; match the existing style; remove only the orphans your own change created.
4. **Define done before starting.** Every task becomes a verifiable goal with its success criterion included in the delegated prompt.

These disciplines feed the router: a task stripped to its smallest verifiable form is cheaper to classify and usually routes lower.

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

## Customization

- **Model lineup changed?** Edit the "Current alias" column in `SKILL.md` — nothing else. Bands, rules, and the adaptation protocol are deliberately model-agnostic. If you installed via npm or git, make the same edit in your clone of this repo too: package updates overwrite the installed copy.
- **Different tier boundaries?** Move work types between the "Route here" cells. Keep the four-band structure: it matches how model families are actually positioned (fast / balanced / deep / flagship).
- **Stricter escalation?** Change rule 2's "one retry, then one tier up" to your taste — e.g., two retries for expensive tiers.
- **House discipline?** The four execution rules are a good default; append your own (e.g., "always run the linter") in the same numbered list.

---

## Verification

The skill ships verified by a baseline/with-skill comparison ("RED/GREEN"):

- **Without the skill**, a small model planning delegations routed an unknown-cause, multi-module debugging task to the flagship tier and improvised an inconsistent answer about model removal.
- **With the skill**, the same model routed that task to T3 (DEEP), kept lookups and summaries at T1, and answered the removal question exactly per the adaptation protocol: "T3 gone → T4 only for genuinely hard work."

To re-verify after editing the skill, run the bundled quiz mechanically (any cheap model works):

```bash
cat test/routing-quiz.txt | claude -p --model haiku
```

Expected: (a) T1, (b) T2, (c) T3, (d) T1, (e) T4 with the removal reasoning, (f) at-least-T2 verification by a non-author citing consequence, (g) inline. Any drift from those answers means your edit broke a rule.

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
