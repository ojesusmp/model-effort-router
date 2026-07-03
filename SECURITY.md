# Security policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `1.3.x` | Yes |
| `< 1.3` | No — upgrade to the latest minor release |

Security fixes are backported only to the most recent minor version line.

## Reporting a vulnerability

If you discover a security issue in `model-effort-router` — for example a way to make the postinstall script write outside the Claude Code skills directory, or skill text that could be abused to steer an orchestrator into destructive behavior — please report it privately.

### How to report

1. Do **not** open a public GitHub issue for security reports. Public issues become visible to anyone immediately.
2. Use GitHub's private vulnerability reporting feature on this repository: open the "Security" tab and follow the prompts under "Report a vulnerability." That submission is visible only to repository maintainers.

### What to include

Please include enough detail for a maintainer to reproduce and assess the issue:

- A clear description of the issue and its impact.
- Steps to reproduce, or a minimal proof of concept.
- The affected version(s) of `model-effort-router` (run `npm view @ojesusmp/model-effort-router version` if unsure).
- Any mitigating factors or workarounds you have identified.

### What to expect

- Acknowledgment within 7 days.
- An initial assessment and proposed remediation timeline within 14 days.
- A fix released as a patch version, with a corresponding CHANGELOG entry crediting the reporter (if they wish to be credited).

## Threat model

`model-effort-router` is a single Markdown instruction file plus a small install script. Its security surface is intentionally tiny:

- **In scope:**
  - `SKILL.md` must remain plain instructions — no executable content, no external references, no data exfiltration, no text that instructs an orchestrator to bypass user permissions or perform destructive actions.
  - `bin/install.mjs` must not write outside `~/.claude/skills/model-effort-router/`, must not execute downloaded code, and must not make network calls.
  - The optional hooks documented in the README must stay read-and-log only (a reminder message and an append-only local ledger).
- **Out of scope:** Issues with the Claude Code platform itself, the models' own behavior, the user's terminal, or third-party skills are not handled here — please report those to their respective maintainers.

## Past advisories

None at this time.
