# Security policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `1.0.x` | Yes |
| `< 1.0` | No (pre-release) |

Security fixes are backported only to the most recent minor version line.

## Reporting a vulnerability

If you discover a security issue in `model-effort-router` â€” for example a way to make the generated HTML execute arbitrary code, leak data, contact an external network, or otherwise behave outside its documented surface â€” please report it privately.

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

`model-effort-router` is a documentation-generation skill. Its security surface is intentionally small:

- **In scope:** Generated HTML must not include external references, must not execute scripts, must not exfiltrate data, must not load fonts or images from the network. The postinstall script must not write outside the user's Claude Code skills directory.
- **Out of scope:** Issues with the Claude Code platform itself, the user's terminal, or third-party skills are not handled here â€” please report those to their respective maintainers.

## Past advisories

None at this time.
