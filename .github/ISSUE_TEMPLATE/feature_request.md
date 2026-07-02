---
name: Feature request
about: Suggest a new feature or improvement.
title: "[Feature] "
labels: enhancement
assignees: ojesusmp
---

## Problem

Describe the user problem this feature would solve. Start with the user, not the solution.

Example: "My team runs Claude Code with a custom in-house model between T2 and T3, and the four-band table gives me no place to put it."

## Proposed solution

Describe what you would like to happen. Be as specific as you can.

## Alternatives considered

Other approaches you thought about and why you did not choose them.

## Compatibility with project goals

Confirm that the proposed feature does not violate any of these non-negotiable goals (see `CONTRIBUTING.md`):

- [ ] Bands stay model-agnostic — no rules written against specific model names.
- [ ] `SKILL.md` stays a single self-contained Markdown instruction file that executes nothing.
- [ ] No unbounded behavior — every retry/escalation/spawn path is bounded by the attempt budget and ends in the terminal state.
- [ ] Trigger phrases stay precise — no generic phrases that would fire on everyday Claude Code usage.

If your proposal does conflict with one of these goals, explain why the conflict is worth it.

## Additional context

Transcripts, ledger excerpts (`~/.claude/router-ledger.jsonl`), related issues, or links to similar features elsewhere.
