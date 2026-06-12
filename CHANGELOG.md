# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
