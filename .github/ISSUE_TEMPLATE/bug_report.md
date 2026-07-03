---
name: Bug report
about: Report something that does not work as documented.
title: "[Bug] "
labels: bug
assignees: ojesusmp
---

## Summary

A one-line description of the bug.

## Bug type

- [ ] Routing misbehavior (the orchestrator routed/escalated/looped against the rules)
- [ ] Quiz drift (the gate no longer produces the expected answers)
- [ ] Install problem (`npm install` / postinstall / marketplace)
- [ ] Documentation error
- [ ] Other

## Environment

- model-effort-router version: (run `npm view @ojesusmp/model-effort-router version` or check `package.json`)
- Install method: (npm / git / Claude marketplace)
- Operating system: (Windows / macOS / Linux + version)
- Node version: (run `node --version`)
- Claude Code version: (run `claude --version`)
- Main-loop model and available model aliases, if the bug is routing-related

## Steps to reproduce

1. ...
2. ...
3. ...

For routing misbehavior, include the task you delegated and the model/tier the orchestrator chose. For quiz drift, paste the gate command and its output.

## Expected behavior

What you expected to happen (cite the rule from `SKILL.md` if applicable).

## Actual behavior

What actually happened. Include error messages or transcript excerpts if relevant.

## Additional context

Anything else that might help — related issues, recent changes to your environment, custom edits to your installed `SKILL.md`, etc.
