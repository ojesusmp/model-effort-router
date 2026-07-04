# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-07-03

### Fixed

- **Plugin install now exposes the main skill.** The `model-effort-router`
  skill lived at the repo root (`SKILL.md`), but Claude Code only
  auto-discovers skills under `skills/<name>/`, so a `/plugin install` only
  registered the companion `skill-hardener` and invoking the router returned
  "Unknown skill". The skill now lives at `skills/model-effort-router/SKILL.md`
  and is picked up by a plain plugin install (no npm postinstall needed).
  Tooling (`bin/install.mjs`, `validate.mjs`, `package.json` files, README,
  CONTRIBUTING) updated to the new path.

## [1.3.0] - 2026-07-02

### Added

- **Failure taxonomy**: every failed delegation is classified as harness,
  prompt, or capability failure before any reaction — only capability
  failures escalate. Fixing a prompt at the same tier replaces the old
  behavior of escalating everything, and permission/policy blocks are
  explicitly "change approach, never retry verbatim."
- **Attempt budget with terminal state** (the anti-loop guarantee): at most
  2 work attempts per tier and 4 work spawns per task; identical prompts are
  never resent after a failure; two identical failures mean wrong diagnosis,
  not insufficient model; and when the ceiling tier fails or the budget is
  spent, the task terminates in a precise "blocked because X" report instead
  of another spawn.
- **Cooperation protocol** ("the cell rule"): scouts feed workers (T1 gathers
  context so higher tiers spend tokens only on the hard core); every
  hand-off/escalation carries a compact brief (goal, done, exact failures,
  remaining question) so no tier re-pays for discovery; agents return
  material (paths, diffs, failing commands) rather than narrative; the
  verifier is never the author; parallel agents get disjoint scopes.
- **Degenerate-lineup rules** in the adaptation protocol: a lineup of one
  model maps every tier to it (discipline unchanged), and an alias rejected
  at spawn time falls back to the nearest neighbor in the same call — a task
  is never stalled on a table fix.
- Quiz questions (i)–(l) covering the terminal state, the hand-off brief,
  the single-model lineup, and prompt-failure (no escalation).

### Hardened (adversarial audit of the first draft)

An independent audit pass against the draft found eight defects — three
rule-vs-rule contradictions, two literal-reading loop risks, one provable
waste path, two undefined situations — all fixed before release:

- Routing rule 2 and the capability-failure entry now describe the same
  ladder (sharpened same-tier retry → one tier up), and a **clear misroute
  jumps straight to the indicated tier** instead of walking the ladder —
  closing the path where a hard task misrouted to T1 burned its whole
  budget without ever reaching the tier that would have succeeded.
- Work-spawn budget raised from 4 to 6, with an explicit tie-break: when
  the remaining budget can't cover both a retry and an escalation,
  escalate.
- The identical-prompt ban now applies to *work* failures only, so it no
  longer contradicts the harness-failure recovery (whose prompt was never
  processed).
- Verification got its own cap (2 verify → fix → re-verify cycles, not
  counted as work spawns), and a verifier's rejection is classified by the
  failure taxonomy instead of falling outside it.
- The delegated-prompt template now requires passing the attempt budget and
  terminal state to any spawn-capable subagent — "iterate until verified"
  without a budget is a license to loop one level down.
- Model-removal collapse covers T2 (and chained removals: keep collapsing
  until a model exists); alias-rejection fallback tries each distinct alias
  at most once per task; a zero-model lineup makes the router inert
  (inline work, discipline intact); an unknown new model name defaults to
  T2 and is re-banded by observation.

A second audit round confirmed all eight fixes and found three residual
defects at the seams of the fixes, also closed before release:

- The budget-propagation requirement in the delegated-prompt template now
  propagates itself, so spawn-capable grandchildren at any depth carry the
  attempt budget and terminal state.
- An escalated author gets one fresh verification cap — once; after that
  the task terminates. Consequence-bearing work that cannot pass
  verification is reported as blocked, never shipped unverified.
- The misroute direct-jump tops out at T3: T4's entry gate (a demonstrably
  failed T3 attempt, or an explicit user request) always holds.

### Repository

- **Bundled companion skill: skill-hardener** (`skills/skill-hardener/`,
  shipped in the npm package and deployed by the installer to
  `~/.claude/skills/skill-hardener/`): the reusable hardening pipeline —
  staleness recon for old skills, five-class gap analysis, rewrite
  discipline, mechanical gate, adversarial audit until dry (own budget: 4
  rounds), cross-model verification, repo sweep — with its own 6-question
  gate verified 6/6 on two model tiers.
- **Ledger dashboard** (`tools/router-dashboard.html`, shipped in the npm
  package): a single self-contained HTML page that reads
  `~/.claude/router-ledger.jsonl` locally (file picker or drag-and-drop — no
  network, no upload) and shows stat tiles, delegations by tier, a stacked
  timeline, and a full table view, with date-range filtering, editable
  relative cost weights, tooltips, dark mode, and a colorblind-validated
  palette. Inherit entries are counted at the T4 weight and the cost index
  is labeled as a relative proxy.
- **CI workflow** (`.github/workflows/ci.yml`): installer dry run, `npm pack`
  dry run, and a consistency validator (`.github/scripts/validate.mjs`) that
  checks SKILL.md structure and frontmatter, version agreement across
  `package.json` / `marketplace.json` / CHANGELOG, and that the README's
  expected answers cover every quiz question.
- **Publish workflow** (`.github/workflows/publish.yml`): publishes to npm
  with provenance when a GitHub release is published (requires an
  `NPM_TOKEN` repository secret; refuses tags that don't match
  `package.json`).
- **Funding file** (`.github/FUNDING.yml`) for GitHub Sponsors.
- Marketplace manifest bumped to 1.3.0 and its plugin description updated
  to cover the anti-loop and cooperation guarantees.

### Fixed

- `CONTRIBUTING.md`, `SECURITY.md`, the pull-request template, and both
  issue templates described a different project (an HTML documentation
  generator). All five rewritten for what this repository actually is —
  goals, threat model, verification steps, and checklists now reference the
  quiz gate, the attempt budget, and the installer instead of generated
  HTML.

### Changed

- Routing rule 2 now binds escalation to the attempt budget and the hand-off
  brief.
- The delegated-prompt template requires "material, not narrative" returns
  and the hand-off brief on escalation.
- The "When the harness misbehaves" section was absorbed into the failure
  taxonomy (same recovery path, unchanged caps).

## [1.2.0] - 2026-06-12

### Added

- **Enforcement hook** (optional, documented in README): a PreToolUse hook
  that flags any agent spawn with no explicit `model` parameter at the moment
  it happens — silent when a tier was chosen. Soft by design so it cannot
  break multi-agent workflows.
- **Measurement ledger** (optional, documented in README): a PostToolUse hook
  that automatically appends one JSON line per delegation (time, model, agent
  type, description) to `~/.claude/router-ledger.jsonl`, turning
  cost-effectiveness from an assumption into auditable data.
- **Harness-misbehaves recovery path** in the skill: a greeting-only or empty
  subagent reply is harness failure, not model failure — retry once at the
  same tier (no escalation), then run headless (`claude -p --model <alias>`),
  then inline as last resort.
- **Disguised-hard heuristic**: a cheap result that will be trusted without
  anyone reading the source material counts as consequence-bearing for
  verification sizing.
- **Limitations section** in the README documenting the boundaries the skill
  cannot fix (policy not guarantee, harness reliability, main-loop scope,
  task-description blindness).
- Quiz question (h) covering the harness-failure recovery rule.

### Changed

- `test/routing-quiz.txt` no longer embeds a copy of the skill text — the
  gate command is now `cat SKILL.md test/routing-quiz.txt | claude -p --model
  haiku`, so the test always runs against the live rules and can never drift.

### Verified

- 8/8 gate run on a fresh low-tier model against the live v1.2.0 SKILL.md,
  including the new harness-failure probe ("retry at haiku, no escalation —
  harness failure, not model failure").
- Both hooks pipe-tested: reminder fires only when `model` is absent; ledger
  line parses with correct fields.

## [1.1.0] - 2026-06-12

### Added

- **Consequence rule for verification** (routing rule 4): anything that
  publishes, ships to production, or is hard to reverse gets at least T2
  verification by a non-author (T3 when the blast radius is real), no matter
  how small the change — a cheap author checked by an equally cheap reviewer
  is a correlated failure.
- **Overhead floor for delegation** (routing rule 5): one-liners and single
  lookups are done inline; a subagent spawn has real fixed cost and delegation
  pays for real work, not micro-tasks.
- **Routing record**: the reason for any escalation is stated in one line of
  the report to the user.
- Bundled mechanical gate test at `test/routing-quiz.txt`
  (`cat test/routing-quiz.txt | claude -p --model haiku`); shipped in the npm
  package.

### Changed

- Maintenance guidance: alias edits on package-installed copies must also be
  made in the source repo (package updates overwrite the installed copy), and
  the routing quiz should be re-run after any edit.

### Verified

- Full 7-question gate run against the verbatim v1.1.0 SKILL.md text on a
  fresh low-tier model: 7/7 correct, including the consequence-verification
  and inline-floor probes.

## [1.0.0] - 2026-06-12

### Added

- Initial release of the **model-effort-router** skill.
- Four-tier routing table (LIGHT / STANDARD / DEEP / FRONTIER) mapping work types
  to the cheapest capable model tier, with stable bands and a single replaceable
  alias column.
- Routing rules: lowest tier that succeeds in one pass, evidence-based escalation
  (one retry, then one tier up), shrink-and-split before routing, verification
  sized like work, main-loop delegation.
- Adaptation protocol: the environment's accepted model aliases are the live
  source of truth; new models are placed by positioning, removed models collapse
  to neighbor tiers, renamed models are followed.
- Execution discipline embedded in every routed task: surface assumptions,
  smallest thing that works, surgical changes, verifiable success criteria.
- Delegated-prompt template and quick examples.
- npm postinstall installer (`bin/install.mjs`), Claude Code plugin marketplace
  manifest, and full repository documentation.

[1.3.0]: https://github.com/ojesusmp/model-effort-router/releases/tag/v1.3.0
[1.2.0]: https://github.com/ojesusmp/model-effort-router/releases/tag/v1.2.0
[1.1.0]: https://github.com/ojesusmp/model-effort-router/releases/tag/v1.1.0
[1.0.0]: https://github.com/ojesusmp/model-effort-router/releases/tag/v1.0.0
