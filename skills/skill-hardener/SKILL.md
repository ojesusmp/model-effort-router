---
name: skill-hardener
description: Use when asked to audit, harden, improve, modernize, refresh, or verify a Claude Code skill (a SKILL.md or a skill repository) — especially a skill written months ago that may reference outdated models, tools, commands, or docs — or when asked to run a skill-hardening pipeline against a skill.
---

# Skill Hardener

A pipeline for taking an existing skill — however old — and making it
current, loop-proof, waste-proof, contradiction-free, and mechanically
verifiable. Run the phases in order; each produces evidence the next
consumes. Do not skip the recon phase for old skills: staleness findings
change what every later phase looks for.

## Phase 0 — Recon and staleness inventory (read everything, change nothing)

Old skills rot in predictable places. Before any edit, read every file in
the skill's directory/repo and build an inventory:

1. **Age markers.** Last commit date, CHANGELOG dates, version numbers.
   Anything older than ~3 months gets the full staleness sweep below.
2. **Model references.** Every model name/alias in the skill, docs, tests,
   and examples, checked against the live environment (the `model` values
   the Agent tool accepts, `claude --version` era). Renamed, retired, or
   superseded models are findings.
3. **Command and tool references.** Every shell command, CLI flag, tool
   name, file path, and URL the skill tells the reader to use — verify each
   still exists and behaves as described. Run the harmless ones.
4. **Doc-reality drift.** Does the README describe the files that actually
   exist? Do templates, contributing guides, and security policies describe
   THIS project? (Copied-from-another-repo boilerplate is a common find.)
   Do version numbers agree across package manifest, marketplace manifest,
   and changelog?
5. **Trigger health.** Does the frontmatter `description` still fire on the
   situations the skill is for, and only those? Too-generic phrases collide
   with everyday usage; too-narrow ones mean the skill never loads.

Output: a written inventory of staleness findings. Report it before
changing anything — the user decides on anything that looks like a scope
change.

## Phase 1 — Gap analysis (the five defect classes)

List defects before fixing any. A defect is a scenario where an agent
*literally following the skill's text* fails. Classify every finding:

- **(a) Unbounded behavior** — any retry/escalate/iterate/spawn path with
  no hard budget or no defined terminal state. "Loop until done" without a
  cap is a defect even when it usually terminates.
- **(b) Undefined behavior** — a plausible situation for which the rules
  give no instruction (the removed middle option, the empty lineup, the
  rejected parameter, the failure that fits no listed category).
- **(c) Provable waste** — double-paid work: escalation that discards prior
  findings, parallel agents with overlapping scopes, identical retries,
  rules whose interaction makes a needed path unreachable.
- **(d) Contradictions** — two rules prescribing conflicting actions for
  the same event. Check every new rule against every old one, especially
  caps vs. mandates ("always verify" vs. "at most N spawns").
- **(e) Environment fragility** — behavior that breaks when models, tools,
  or platforms change. Rules must be written against stable abstractions
  (bands, roles, capabilities) with concrete names isolated in one
  replaceable spot.

Output: the numbered defect list with, for each, the quoted text at fault
and a one-line failure scenario. This list is the work order and goes in
the eventual PR body.

## Phase 2 — Rewrite (fix rules, don't append disclaimers)

- **Rewrite the defective rule; never bolt a caveat onto it.** Skills die
  by accretion — if every fix adds a paragraph, the skill bloats until
  nobody (human or model) holds it all. Target: the hardened skill is not
  materially longer than the original unless it was missing whole
  mechanisms.
- Every loop-shaped path gets a **hard budget and a terminal state** whose
  output is a precise "blocked because X" report — and if the skill lets
  its user spawn further agents, the budget requirement must **propagate
  itself** into those prompts, or the loop reappears one level down.
- Every multi-step or multi-agent flow gets **evidence-carrying hand-offs**
  (goal, what's done, exact failures verbatim, the remaining question) so
  no step re-pays for a previous step's discovery.
- Every failure-response rule distinguishes **why** the failure happened
  (infrastructure vs. bad instruction vs. genuine capability) — the
  responses differ and conflating them wastes effort.
- Concrete names (models, versions, tools) move to **one replaceable
  table/spot**; the rules reference the abstraction.

## Phase 3 — Mechanical gate (build it if it's missing)

The gate is what keeps the skill verifiable after you're gone:

- A test file of scenario questions with documented expected answers, run
  by piping the **live skill text** plus the questions to a cheap model:
  `cat SKILL.md test/quiz.txt | claude -p --model <cheap-alias>`. Never
  embed a copy of the skill in the test — copies drift.
- **Every behavioral rule gets a question that would catch its
  regression**, including the rules you just added. A rule with no failing
  test for its absence is a rule you can't protect.
- Expected answers live in the README next to the run command. Any drift
  from them means an edit broke a rule.

## Phase 4 — Adversarial audit until dry (the core loop)

Spawn an independent auditor agent per round. The prompt must contain:

> Read <skill file> in full. Try to BREAK it. Hunt specifically for:
> (1) any scenario where an agent following these rules literally loops,
> stalls, or spawns without terminating; (2) provable waste (double-paid
> work, unreachable-but-needed paths); (3) contradictions between rules;
> (4) plausible situations with no instruction; (5) breakage under
> environment change (models/tools added, renamed, removed, down to one,
> down to zero). For each candidate, verify against the exact text and
> QUOTE the rule that fails or is missing — discard anything the file
> actually covers. No style nitpicks, no feature suggestions. Return
> confirmed defects with quotes and one-line failure scenarios, or "NO
> CONFIRMED DEFECTS".

Rules of the loop:

1. Fix all confirmed findings, then run **another full round** that both
   re-verifies each fix (verdict per finding, quoting the fixed text) and
   hunts for **new defects at the seams of the fixes** — fixes introduce
   defects where they touch other rules; that is where round 2 finds
   things.
2. **Stop condition: a round returns zero**, not "we did a review."
3. **The loop has its own budget**: if 4 rounds haven't converged, stop
   and report the un-converged findings to the user — the skill likely
   needs a redesign, not another patch. (This pipeline obeys its own
   no-unbounded-loops rule.)
4. Record the full audit trail (per round: found, fixed, confirmed) in the
   CHANGELOG — it is the proof of hardening and the map for the next
   maintainer.

## Phase 5 — Cross-model verification

Run the gate on at least two different model tiers and require identical
expected answers. A skill that only one model reads correctly is written
for that model, not for the platform. If a cheap model misreads a rule,
the fix is almost always clearer skill text, not a bigger model.

## Phase 6 — Repo sweep

- Docs describe the current files and behavior; kill copied boilerplate.
- Versions agree everywhere they appear (manifest(s), changelog, docs).
- CI validates everything mechanical: structure, frontmatter, version
  consistency, gate-file/README sync. What CI can't run (the model gate),
  CONTRIBUTING requires contributors to run.
- Issue/PR templates ask for the evidence this pipeline produces (gate
  output, quoted rule text for behavior bugs).

## Phase 7 — Ship with evidence

- Commits state what was verified and how, not just what changed.
- The PR body carries: the staleness inventory, the gap analysis, the
  audit trail (rounds and counts), and the gate results per model.
- Never publish/release as part of hardening unless asked — the PR is the
  deliverable; releasing is the user's call.

## Calibration — size the pipeline to the skill

| Skill | Pipeline |
|---|---|
| Personal one-pager | Phase 0 + 1, one audit round, gate optional |
| Team-shared skill | All phases, 2-round minimum audit |
| Published package (npm/marketplace) | All phases, audit until dry, cross-model gate, full repo sweep |

Delegation: if a model-routing skill (e.g. model-effort-router) is
installed, route this pipeline's own agents through it — auditors are
deep-review work, gate runs are cheap, recon file-reading is cheap. Give
parallel auditors disjoint defect classes, and always pass each agent the
task, success criterion, scope limit, and what to return.

## Anti-patterns (each one observed in the wild)

- **Appending caveats instead of rewriting rules** — the skill bloats and
  the contradiction usually survives.
- **Stopping after one audit round** — round 2 exists because fixes create
  seam defects; skipping it ships them.
- **A gate that embeds a copy of the skill text** — the copy drifts and
  the gate silently tests dead rules.
- **Accepting auditor findings without quoted text** — unverified findings
  are often hallucinated; the quote requirement kills them.
- **"Modernizing" by swapping model names only** — names are Phase 0; the
  defects that matter are in Phases 1–4.
- **Hardening the skill but not its docs** — six months later the README
  contradicts the rules and someone "fixes" the rules back.
