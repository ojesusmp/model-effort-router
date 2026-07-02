#!/usr/bin/env node
// Repo consistency checks that need no API access. The behavioral gate
// (cat SKILL.md test/routing-quiz.txt | claude -p --model haiku) still runs
// locally per CONTRIBUTING.md — this script catches everything mechanical.

import { readFileSync } from "node:fs";

let failures = 0;
function check(name, ok, detail = "") {
  if (ok) {
    console.log(`ok   ${name}`);
  } else {
    failures++;
    console.error(`FAIL ${name}${detail ? ` — ${detail}` : ""}`);
  }
}

const skill = readFileSync("SKILL.md", "utf8");
const readme = readFileSync("README.md", "utf8");
const changelog = readFileSync("CHANGELOG.md", "utf8");
const quiz = readFileSync("test/routing-quiz.txt", "utf8");
const pkg = JSON.parse(readFileSync("package.json", "utf8"));
const marketplace = JSON.parse(
  readFileSync(".claude-plugin/marketplace.json", "utf8")
);

// --- SKILL.md structure ---
const lines = skill.split("\n");
check("SKILL.md under 400 lines", lines.length < 400, `${lines.length} lines`);

const fmMatch = skill.match(/^---\n([\s\S]*?)\n---/);
check("SKILL.md has YAML frontmatter", !!fmMatch);
if (fmMatch) {
  check("frontmatter has no tabs", !fmMatch[1].includes("\t"));
  check("frontmatter has name", /^name:\s*\S+/m.test(fmMatch[1]));
  check("frontmatter has description", /^description:\s*\S+/m.test(fmMatch[1]));
}

for (const section of [
  "## Tier table",
  "## Routing rules",
  "## Adaptation protocol",
  "## Execution discipline",
  "## Failure taxonomy",
  "## Attempt budget",
  "## Cooperation protocol",
  "## Delegated-prompt template",
]) {
  check(`SKILL.md section present: ${section}`, skill.includes(section));
}

for (const tier of ["T1 — LIGHT", "T2 — STANDARD", "T3 — DEEP", "T4 — FRONTIER"]) {
  check(`tier table row: ${tier}`, skill.includes(tier));
}

// --- Version consistency ---
const clVersion = (changelog.match(/^## \[(\d+\.\d+\.\d+)\]/m) || [])[1];
check(
  "package.json version == marketplace metadata version",
  pkg.version === marketplace.metadata.version,
  `${pkg.version} vs ${marketplace.metadata.version}`
);
check(
  "package.json version == marketplace plugin version",
  pkg.version === marketplace.plugins[0].version,
  `${pkg.version} vs ${marketplace.plugins[0].version}`
);
check(
  "package.json version == newest CHANGELOG heading",
  pkg.version === clVersion,
  `${pkg.version} vs ${clVersion}`
);

// --- Quiz / README sync ---
const quizLetters = [...quiz.matchAll(/^\((\w)\)/gm)].map((m) => m[1]);
check("quiz has questions", quizLetters.length > 0);
const expectedBlock = readme.match(/Expected:\s*([\s\S]*?)Any drift/);
check("README lists expected quiz answers", !!expectedBlock);
if (expectedBlock) {
  const readmeLetters = [...expectedBlock[1].matchAll(/\((\w)\)/g)].map(
    (m) => m[1]
  );
  check(
    "README expected answers cover every quiz question",
    quizLetters.every((l) => readmeLetters.includes(l)),
    `quiz: ${quizLetters.join(",")} — readme: ${readmeLetters.join(",")}`
  );
}

// --- Packaged files exist ---
check(
  "package.json files list includes SKILL.md and test/",
  pkg.files.includes("SKILL.md") && pkg.files.includes("test/")
);

if (failures) {
  console.error(`\n${failures} check(s) failed`);
  process.exit(1);
}
console.log("\nall checks passed");
