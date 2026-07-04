## Summary

A one or two sentence description of what this pull request changes and why.

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Documentation update
- [ ] Skill behavior change (`SKILL.md`)
- [ ] Install script change (`bin/install.mjs`)
- [ ] Other (please describe)

## Linked issue

Closes #(issue number) — or "N/A" if no issue was filed.

## Verification

Confirm that the relevant checks from `CONTRIBUTING.md` were run. Tick all that apply:

- [ ] `skills/model-effort-router/SKILL.md` changes: ran the quiz gate (`cat skills/model-effort-router/SKILL.md test/routing-quiz.txt | claude -p --model haiku`) and all answers match the expected list in the README; file under ~400 lines; frontmatter tab-free with trigger description intact.
- [ ] Rule additions/changes: added or updated a quiz question covering the change, and updated the README's expected answers.
- [ ] `bin/install.mjs` changes: ran `node bin/install.mjs --dry-run` and `npm pack --dry-run`; both produced expected output.
- [ ] Version metadata: `package.json`, `.claude-plugin/marketplace.json`, and the newest `CHANGELOG.md` heading agree (when bumping a version).
- [ ] Updated `CHANGELOG.md` under `## [Unreleased]` describing the change.

## Compatibility with project goals

- [ ] Bands stay model-agnostic — model names appear only in the tier table's alias column.
- [ ] `SKILL.md` stays a single self-contained Markdown instruction file — executes nothing, references nothing external.
- [ ] Every retry/escalation/spawn path remains bounded by the attempt budget and ends in the terminal state.
- [ ] Trigger phrases remain precise.

## Quiz gate output

For `SKILL.md` changes, paste the gate run's answers (or the relevant subset).

## Additional notes

Anything reviewers should know — tradeoffs, follow-up work, related discussion, etc.
