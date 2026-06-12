# Contributing to model-effort-router

Thanks for your interest in improving `model-effort-router`. This document explains how to propose changes, what the project's design constraints are, and how the maintainers review contributions.

## Project goals

Before contributing, make sure your change aligns with the project's primary goals â€” these are non-negotiable and any contribution that violates them will be rejected regardless of how well-written it is.

1. **Output portability.** The generated HTML file must work offline, on any operating system, in any modern browser, without any external resources, network calls, JavaScript libraries, or web fonts. Anything that adds a runtime dependency to the generated output is out of scope.
2. **Plain-language output.** The HTML should be readable at an 18-year-old reading level. Jargon goes in the glossary.
3. **Trigger precision.** Auto-fire trigger phrases must remain narrow. Adding a generic phrase like `explain this` is rejected by default because it collides with everyday Claude Code usage.
4. **Honest provenance.** Inferred items must render as unconfirmed. Removing the two-tier schema or the `.pill--inferred` styling is rejected.

## Ways to contribute

- **Bug reports** â€” open an issue using the bug template.
- **Feature requests** â€” open an issue using the feature template. Describe the user problem first, then propose a solution.
- **Pull requests** â€” small, focused, with tests or a manual verification plan.
- **Documentation** â€” README, CHANGELOG, glossary improvements are always welcome.
- **Template improvements** â€” visual refinements that stay within the no-JS / no-external-resources rule.

## Pull request workflow

1. Fork the repo and create a feature branch from `main`.
2. Make your change. Keep diffs small and focused â€” one logical change per pull request.
3. Update `CHANGELOG.md` under an `## [Unreleased]` heading describing what you changed.
4. Run the verification steps below.
5. Open a pull request against `main` using the provided template.
6. Be patient â€” review may take a few days. We optimize for thoughtful review over speed.

## Verification before opening a pull request

For changes that touch `templates/base.html`:

- Open the file directly in a browser and confirm all ten sections render with placeholder content.
- Toggle your operating system between light and dark mode and confirm both look readable.
- Print preview and confirm the navigation hides and content paginates cleanly.
- Run a grep for forbidden external references and confirm zero matches:

```bash
grep -nE 'https?://|cdn\.|<script src|<link|@import url\(http' templates/base.html
```

For changes that touch `SKILL.md`:

- Confirm the file is still under ~400 lines.
- Confirm the YAML frontmatter has no tabs and the `description` field still contains exactly the five auto-fire trigger phrases verbatim.
- Confirm the two-tier `confirmed_*`/`inferred_*` schema is intact for the fabrication-prone arrays.

For changes that touch `bin/install.mjs`:

- Run `node bin/install.mjs --dry-run` from the package root and confirm it lists every file in `files` from `package.json`.
- Run `npm pack --dry-run` and confirm the tarball contents match expectations.

## Coding conventions

- Use 2-space indentation in JavaScript and HTML.
- Prefer plain ASCII characters in source. The output HTML can contain Unicode where the glossary needs it.
- Match the existing code style. If you would do it differently personally, match the file you are editing.
- Do not add new top-level dependencies to `package.json`. The package is intentionally zero-dependency.
- Do not add new top-level files unless you are also updating `package.json` `files` and the README.

## Reporting security issues

Do **not** open a public issue for security-related reports. Follow the process in [SECURITY.md](./SECURITY.md).

## Code of conduct

By participating in this project, you agree to abide by the [Contributor Covenant](./CODE_OF_CONDUCT.md).
