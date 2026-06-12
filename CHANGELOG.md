# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/ojesusmp/model-effort-router/releases/tag/v1.0.0
