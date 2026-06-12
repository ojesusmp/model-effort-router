## Summary

A one or two sentence description of what this pull request changes and why.

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Documentation update
- [ ] Template visual change (`templates/base.html`)
- [ ] Skill behavior change (`SKILL.md`)
- [ ] Install script change (`bin/install.mjs`)
- [ ] Other (please describe)

## Linked issue

Closes #(issue number) â€” or "N/A" if no issue was filed.

## Verification

Confirm that the relevant checks from `CONTRIBUTING.md` were run. Tick all that apply:

- [ ] Template changes: opened `templates/base.html` in a browser, verified all 10 sections render, toggled light/dark, ran print preview, and confirmed no external references via grep.
- [ ] `SKILL.md` changes: confirmed file is under ~400 lines, YAML frontmatter has no tabs, description contains all five auto-fire trigger phrases verbatim, two-tier schema intact.
- [ ] `bin/install.mjs` changes: ran `node bin/install.mjs --dry-run` and `npm pack --dry-run`; both produced expected output.
- [ ] Updated `CHANGELOG.md` under `## [Unreleased]` describing the change.

## Compatibility with project goals

- [ ] Generated HTML stays self-contained â€” no external resources, no JavaScript libraries, no network calls.
- [ ] Generated HTML remains readable at an 18-year-old reading level.
- [ ] Trigger phrases remain precise.
- [ ] Two-tier confirmed-versus-inferred schema is intact.

## Screenshots or output samples

If your change affects the rendered HTML, include a screenshot or a link to a sample output file.

## Additional notes

Anything reviewers should know â€” tradeoffs, follow-up work, related discussion, etc.
