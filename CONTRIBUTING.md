# Contributing to model-effort-router

Thanks for your interest in improving `model-effort-router`. This document explains how to propose changes, what the project's design constraints are, and how the maintainers review contributions.

## Project goals

Before contributing, make sure your change aligns with the project's primary goals — these are non-negotiable and any contribution that violates them will be rejected regardless of how well-written it is.

1. **Model-agnostic bands.** The four-tier structure (LIGHT / STANDARD / DEEP / FRONTIER) must survive any model launch, rename, or retirement. Rules are written against *bands*, never against specific model names; model names appear only in the single "current alias" column of the tier table.
2. **Single self-contained instruction file.** `SKILL.md` is plain Markdown that executes nothing, references no external resources, and phones home to no one. Anything that adds runtime behavior to the skill itself is out of scope (optional hooks live in the README as user-installed snippets).
3. **No unbounded behavior.** Every rule that can trigger a retry, an escalation, or a spawn must be bounded by the attempt budget and terminate in the defined terminal state. A contribution that reintroduces an open-ended loop ("keep trying until it works") is rejected by default.
4. **Trigger precision.** The frontmatter `description` controls when the skill fires. It must stay scoped to delegation/model-choice moments; generic phrases that would fire on everyday Claude Code usage are rejected.
5. **Verified, not vibed.** Any change to routing behavior must pass the bundled quiz gate (below) before it ships, and behavior-affecting additions should add a quiz question covering them.

## Ways to contribute

- **Bug reports** — open an issue using the bug template. Routing misbehavior, quiz drift, and installer problems all count.
- **Feature requests** — open an issue using the feature template. Describe the user problem first, then propose a solution.
- **Pull requests** — small, focused, with the verification steps below actually run.
- **Documentation** — README, CHANGELOG, and example improvements are always welcome.
- **Adversarial findings** — if you can construct a scenario where a literal rule-following orchestrator loops, stalls, wastes tokens, or faces two conflicting instructions, that's a bug. File it with the quoted rule text and the scenario.

## Pull request workflow

1. Fork the repo and create a feature branch from `main`.
2. Make your change. Keep diffs small and focused — one logical change per pull request.
3. Update `CHANGELOG.md` under an `## [Unreleased]` heading describing what you changed.
4. Run the verification steps below.
5. Open a pull request against `main` using the provided template.
6. Be patient — review may take a few days. We optimize for thoughtful review over speed.

## Verification before opening a pull request

For changes that touch `skills/model-effort-router/SKILL.md`:

- Run the quiz gate against the live file and confirm all answers match the expected list in the README's [Verification](./README.md#verification) section:

```bash
cat skills/model-effort-router/SKILL.md test/routing-quiz.txt | claude -p --model haiku
```

- Confirm the file is still under ~400 lines.
- Confirm the YAML frontmatter has no tabs and the `description` field still describes the same delegation/model-choice triggers.
- If your change adds or alters a routing rule, add or update a quiz question that would catch a regression of it, and update the expected answers in the README.

For changes that touch `bin/install.mjs`:

- Run `node bin/install.mjs --dry-run` from the package root and confirm it lists every file in `files` from `package.json`.
- Run `npm pack --dry-run` and confirm the tarball contents match expectations.

For changes that touch versioned metadata:

- Keep `package.json`, `.claude-plugin/marketplace.json` (both `metadata.version` and the plugin entry), and the newest `CHANGELOG.md` heading on the same version number.

## Coding conventions

- Use 2-space indentation in JavaScript and JSON.
- Prefer plain ASCII in source files.
- Match the existing style. If you would do it differently personally, match the file you are editing.
- Do not add dependencies to `package.json`. The package is intentionally zero-dependency.
- Do not add new top-level files unless you are also updating `package.json` `files` (if they should ship) and the README.

## Reporting security issues

Do **not** open a public issue for security-related reports. Follow the process in [SECURITY.md](./SECURITY.md).

## Code of conduct

By participating in this project, you agree to abide by the [Contributor Covenant](./CODE_OF_CONDUCT.md).
