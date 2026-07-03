# skill-hardener

> Point it at any Claude Code skill — including one written six months or a
> year ago — and get back a modernized, loop-proof, contradiction-free,
> mechanically verified version, with the evidence to prove it.

**skill-hardener** is a Claude Code skill that packages a complete
skill-hardening pipeline: staleness recon → gap analysis against five defect
classes → rewrite discipline → a mechanical verification gate → adversarial
audit rounds until one comes back empty → cross-model checks → a full repo
sweep → a PR that carries all the evidence.

It is the distilled method that took **model-effort-router** from a good
draft to a release hardened through three adversarial audit rounds (8
defects found and fixed, then 3 seam defects, then zero) with a 12-question
gate passing on two model tiers.

---

## Install

The skill is a single folder. Copy it into your Claude Code skills
directory:

```bash
# macOS / Linux
mkdir -p ~/.claude/skills/skill-hardener/test
cp SKILL.md ~/.claude/skills/skill-hardener/
cp test/hardener-quiz.txt ~/.claude/skills/skill-hardener/test/
cp README.md ~/.claude/skills/skill-hardener/
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\skill-hardener\test"
Copy-Item SKILL.md,README.md "$env:USERPROFILE\.claude\skills\skill-hardener\"
Copy-Item test\hardener-quiz.txt "$env:USERPROFILE\.claude\skills\skill-hardener\test\"
```

**Verify the install:** open a new Claude Code conversation and ask
*"which skill would you use to audit an old skill?"* — it should name
skill-hardener.

**Optional — make it a repo like model-effort-router:** create a new GitHub
repo with these three files plus a copy of model-effort-router's
`bin/install.mjs` and `package.json` (change the name and the copied file
list), and you get the same `npm install -g` distribution, marketplace
manifest pattern, and CI setup. The model-effort-router repo is the
reference implementation of that packaging.

---

## Usage

In Claude Code, from the directory of the skill you want to improve (or
pointing at it):

```
Harden this skill using the skill-hardener pipeline.
```

```
Audit ~/.claude/skills/my-old-skill — it was written last year and I want
it modernized and verified.
```

```
Run phases 0 and 1 of skill-hardener on this repo and report the findings
before changing anything.
```

The frontmatter triggers on: audit / harden / improve / modernize /
refresh / verify a skill. You can also invoke it explicitly by name.

### What you get back

1. **A staleness inventory** — outdated model names, dead commands, doc
   drift, version mismatches, boilerplate copied from other projects.
2. **A gap analysis** — numbered defects in five classes (unbounded
   behavior, undefined behavior, provable waste, contradictions,
   environment fragility), each with the quoted text at fault.
3. **The hardened skill** — rules rewritten (not caveated), every loop
   bounded with a terminal state, hand-offs carrying evidence, concrete
   names isolated in one replaceable spot.
4. **A mechanical gate** — a quiz file + expected answers, runnable forever
   with `cat SKILL.md test/quiz.txt | claude -p --model haiku`.
5. **An audit trail** — adversarial rounds run until one found nothing,
   recorded in the CHANGELOG.
6. **A PR** with all of the above as its body.

### Old skills (the six-months-later case)

This is the primary use case the pipeline is built for. Phase 0 exists
because stale skills fail differently from badly-designed ones: the rules
may be fine while every concrete reference around them has rotted. The
pipeline checks model names against the **live** environment (never a
memorized list), runs the harmless commands the skill mentions to see if
they still work, and diffs the docs against the actual file tree. Only
after that inventory does defect-hunting start — with the staleness
findings feeding what the auditors look for.

---

## Requirements

- **Claude Code** with the `claude` CLI on PATH (used for the mechanical
  gate: `claude -p --model <alias>`).
- **Git** — the pipeline works on a branch and delivers a PR. It never
  releases or publishes on its own.
- Subagent spawning (the Agent tool) available, for the adversarial audit
  rounds. Without it, the pipeline still runs — audits happen inline, which
  is weaker (less independence) but documented as such in the report.
- Optional but recommended: **model-effort-router** installed, so the
  pipeline's own agents are routed cost-effectively (recon cheap, auditors
  deep, gate runs cheap).

## Cost expectations

A published-package hardening (all phases, audit until dry) is roughly:
2–4 auditor agent runs plus 2–4 cheap gate runs plus the main-loop work.
For a personal one-page skill, the calibration table in SKILL.md cuts that
to one audit round and an optional gate — don't pay the full pipeline for a
skill only you use.

## Verifying this skill itself

skill-hardener ships with its own gate (it follows its own rules):

```bash
cat SKILL.md test/hardener-quiz.txt | claude -p --model haiku
```

Expected answers:

- **(a)** Run Phase 0 recon first — inventory all staleness (models,
  commands, docs, versions) before editing anything; the name fix is one
  finding in it, not the task.
- **(b)** No — run another full round to re-verify the 5 fixes and hunt for
  new defects at the seams of the fixes; stop only when a round returns
  zero.
- **(c)** No — findings must quote the exact text that fails or is missing;
  unquoted findings are discarded (often hallucinated).
- **(d)** Rewrite the rule — appending caveats bloats the skill and usually
  leaves the contradiction alive.
- **(e)** No fifth round — the loop's own budget is 4; stop and report the
  un-converged findings: the skill needs a redesign, not another patch.
- **(f)** No — a pasted copy drifts from the live skill and silently tests
  dead rules; the gate must concatenate the live SKILL.md at run time.

Any drift from those answers means an edit broke the pipeline.

## FAQ

**Does it change my skill's behavior or just its text?**
Both, where needed: Phase 2 rewrites defective rules (behavior), Phase 6
fixes everything around them (docs, versions, CI). Every behavior change
lands with a gate question that would catch its regression.

**Can it run on a skill with no tests at all?**
Yes — Phase 3 *builds* the gate if it's missing. That's usually the highest
value single change for an old skill.

**Will it make my skill longer?**
It shouldn't. The rewrite discipline targets equal-or-shorter unless whole
mechanisms (budget, terminal state, gate) were missing. Bloat is listed as
an anti-pattern.

**What if the audit never converges?**
The audit loop has its own hard budget (4 rounds). If it doesn't converge,
you get the un-converged findings and a recommendation to redesign — the
pipeline obeys its own no-unbounded-loops rule.

**Is this tied to specific Claude models?**
No. Model names are checked against the live environment at run time, and
the pipeline's own delegation advice is written against tiers, not names.

## Credits

Method developed while hardening
[model-effort-router](https://github.com/ojesusmp/model-effort-router) —
that repo's v1.3.0 CHANGELOG is a worked example of the full pipeline's
output.

## License

MIT
