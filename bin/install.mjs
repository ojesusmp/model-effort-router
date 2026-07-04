#!/usr/bin/env node
// Postinstall: copy model-effort-router skill files into the user's Claude Code skills dir.
// Cross-platform (Windows / macOS / Linux). Idempotent. Safe to re-run.
// Skip in CI and skip when running inside the source repo itself.

import { existsSync, mkdirSync, copyFileSync } from "node:fs";
import { homedir, platform } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkgRoot = resolve(__dirname, "..");

const DRY_RUN = process.argv.includes("--dry-run");

function log(msg) {
  process.stdout.write(`[model-effort-router install] ${msg}\n`);
}
function warn(msg) {
  process.stderr.write(`[model-effort-router install] WARN: ${msg}\n`);
}

// Skip in CI environments and during source repo development
if (process.env.CI === "true" || process.env.MER_SKIP_POSTINSTALL === "1") {
  log("CI or MER_SKIP_POSTINSTALL set — skipping install copy.");
  process.exit(0);
}

// Detect if running inside the source repo itself (avoid copying repo to skills dir)
if (existsSync(join(pkgRoot, ".git"))) {
  log("Running inside source repo — skipping install copy (use git clone for dev).");
  process.exit(0);
}

const skillsRoot = join(homedir(), ".claude", "skills");
const targetRoot = join(skillsRoot, "model-effort-router");
const hardenerRoot = join(skillsRoot, "skill-hardener");

function copyFileIfExists(srcRel, destDir, srcBase = "") {
  const s = join(pkgRoot, srcBase, srcRel);
  if (!existsSync(s)) {
    warn(`source missing: ${join(srcBase, srcRel)}`);
    return;
  }
  const d = join(destDir, srcRel);
  if (DRY_RUN) {
    log(`would copy: ${s} -> ${d}`);
    return;
  }
  mkdirSync(dirname(d), { recursive: true });
  copyFileSync(s, d);
}

try {
  log(`platform: ${platform()}`);
  log(`source:   ${pkgRoot}`);
  log(`target:   ${targetRoot}`);
  if (DRY_RUN) log("DRY RUN — no files will be written");

  if (!DRY_RUN && !existsSync(targetRoot)) {
    mkdirSync(targetRoot, { recursive: true });
  }

  copyFileIfExists("SKILL.md", targetRoot, "skills/model-effort-router");
  copyFileIfExists("README.md", targetRoot);
  copyFileIfExists("LICENSE", targetRoot);
  copyFileIfExists("CHANGELOG.md", targetRoot);

  // Bundled companion skill: skill-hardener
  copyFileIfExists("SKILL.md", hardenerRoot, "skills/skill-hardener");
  copyFileIfExists("README.md", hardenerRoot, "skills/skill-hardener");
  copyFileIfExists("test/hardener-quiz.txt", hardenerRoot, "skills/skill-hardener");

  log("done. Skills installed at: " + targetRoot + " and " + hardenerRoot);
  log("model-effort-router activates when Claude Code delegates work; skill-hardener when auditing/hardening a skill.");
} catch (err) {
  warn("install failed: " + (err && err.message ? err.message : String(err)));
  warn("You can manually copy files from " + pkgRoot + " to " + targetRoot);
  // Do not fail the npm install — skill copy is best-effort
  process.exit(0);
}
