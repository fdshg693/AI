import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { buildPublication } from "../scripts/build-catalog.mjs";
import { discoverSkills, parseSkillDocument } from "../scripts/publication-core.mjs";
import { validatePublication } from "../scripts/validate-publication.mjs";

async function fixtureRepo() {
  const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), "skill-site-test-"));
  const skillRoot = path.join(root, "tool", "plugin", "skills");
  await fs.promises.mkdir(path.join(skillRoot, "parent", "child"), { recursive: true });
  await fs.promises.mkdir(path.join(skillRoot, "duplicate"), { recursive: true });
  await fs.promises.writeFile(path.join(skillRoot, "parent", "SKILL.md"), "---\nname: same-name\ndescription: parent\nmeta:\n  status: stable\n---\n# Parent\n");
  await fs.promises.writeFile(path.join(skillRoot, "parent", "child", "SKILL.md"), "---\nname: same-name\ndescription: child\nmeta:\n  status: experimental\n---\n# Child\n");
  await fs.promises.writeFile(path.join(skillRoot, "parent", ".env"), "SECRET=true\n");
  await fs.promises.writeFile(path.join(skillRoot, "parent", ".ENV"), "SECRET=true\n");
  await fs.promises.writeFile(path.join(skillRoot, "parent", ".env.example"), "SECRET=false\n");
  await fs.promises.writeFile(path.join(skillRoot, "parent", "reference.md"), "reference");
  await fs.promises.writeFile(path.join(skillRoot, "duplicate", "SKILL.md"), "---\nname: same-name\ndescription: duplicate\nmeta:\n  status: future\n---\n");
  return { root, registry: [{ id: "fixture", tool: "Fixture Tool", plugin: "fixture", root: "tool/plugin/skills" }] };
}

test("parses known, unset, and unknown status values", () => {
  assert.equal(parseSkillDocument("---\nname: a\ndescription: b\n---\nbody", "a").status.key, "unset");
  assert.equal(
    parseSkillDocument("---\nname: a\ndescription: b\nmeta:\n  status: stable\n---\nbody", "a").status.key,
    "stable",
  );
  assert.equal(
    parseSkillDocument("---\nname: a\ndescription: b\nmeta:\n  status: future\n---\nbody", "a").status.key,
    "unknown",
  );
});

test("normalizes the meta block to always have all 9 keys, backfilling defaults", () => {
  const noMeta = parseSkillDocument("---\nname: a\ndescription: b\n---\nbody", "a").meta;
  assert.deepEqual(Object.keys(noMeta).sort(), [
    "dependencies",
    "description",
    "requiresEnv",
    "requiresHooks",
    "requiresInstall",
    "requiresRepoTools",
    "requiresSkills",
    "status",
    "version",
  ]);
  assert.equal(noMeta.status, "draft");
  assert.equal(noMeta.requiresSkills, "none");

  const withMeta = parseSkillDocument(
    "---\nname: a\ndescription: b\nmeta:\n  status: stable\n  requires_skills: aim-cli, aim-ask\n  requires_repo_tools: tools/aim\n---\nbody",
    "a",
  ).meta;
  assert.equal(withMeta.status, "stable");
  assert.equal(withMeta.requiresSkills, "aim-cli, aim-ask");
  assert.equal(withMeta.requiresRepoTools, "tools/aim");
});

test("publishes nested skills independently and excludes only .env files", async () => {
  const fixture = await fixtureRepo();
  const output = path.join(fixture.root, "output");
  const result = await buildPublication({
    repoRoot: fixture.root,
    registry: fixture.registry,
    generatedRoot: path.join(output, "generated"),
    downloadRoot: path.join(output, "downloads"),
    aiIndexPath: path.join(output, "ai-index.json"),
    searchIndexPath: path.join(output, "search-index.json"),
  });
  assert.equal(result.catalog.skills.length, 3);
  assert.equal(new Set(result.catalog.skills.map((skill) => skill.id)).size, 3);
  const parent = result.catalog.skills.find((skill) => skill.name === "same-name" && skill.description === "parent");
  assert.ok(parent.files.some((file) => file.path === ".env.example"));
  assert.ok(!parent.files.some((file) => file.path.toLowerCase() === ".env"));
  const archive = await fs.promises.readFile(path.join(output, parent.download));
  assert.match(archive.toString("binary"), /PK\x03\x04/);
  assert.equal((await discoverSkills({ repoRoot: fixture.root, registry: fixture.registry })).warnings.length, 1);

  assert.equal(result.aiIndex.schemaVersion, 1);
  assert.equal(result.aiIndex.skills.length, 3);
  const aiParent = result.aiIndex.skills.find((skill) => skill.name === "same-name" && skill.description === "parent");
  assert.deepEqual(Object.keys(aiParent).sort(), ["description", "name", "path", "plugin", "status", "tool"]);
  assert.equal(aiParent.path, parent.path);
  assert.equal(aiParent.tool, parent.tool);
  assert.equal(aiParent.plugin, parent.plugin);
  assert.deepEqual(aiParent.status, { key: parent.status.key });
});

test("rejects malformed frontmatter", () => {
  assert.throws(() => parseSkillDocument("---\nname: [broken\n---\n", "broken"), /invalid YAML frontmatter/);
});

test("ignores SKILL.md files outside registered roots instead of erroring", async () => {
  const fixture = await fixtureRepo();
  await fs.promises.mkdir(path.join(fixture.root, "unregistered"), { recursive: true });
  await fs.promises.writeFile(path.join(fixture.root, "unregistered", "SKILL.md"), "---\nname: x\ndescription: y\n---\n");
  const { skills } = await discoverSkills({ repoRoot: fixture.root, registry: fixture.registry });
  assert.equal(skills.length, 3);
  assert.ok(!skills.some((skill) => skill.id.startsWith("unregistered")));
});

test("overrides can exclude a registered skill or an entire registered source", async () => {
  const fixture = await fixtureRepo();
  const excludedSkill = await discoverSkills({
    repoRoot: fixture.root,
    registry: fixture.registry,
    overrides: { excludeSkills: ["tool/plugin/skills/duplicate/SKILL.md"] },
  });
  assert.equal(excludedSkill.skills.length, 2);
  assert.ok(!excludedSkill.skills.some((skill) => skill.id === "tool/plugin/skills/duplicate/SKILL.md"));

  const excludedSource = await discoverSkills({
    repoRoot: fixture.root,
    registry: fixture.registry,
    overrides: { excludeSources: ["fixture"] },
  });
  assert.equal(excludedSource.skills.length, 0);
});

test("resolves requires_skills to unique/none/multiple matches, and requires_repo_tools to existing/missing paths", async () => {
  const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), "skill-site-test-"));
  const skillRoot = path.join(root, "tool", "plugin", "skills");
  await fs.promises.mkdir(path.join(skillRoot, "target"), { recursive: true });
  await fs.promises.mkdir(path.join(skillRoot, "dup-a"), { recursive: true });
  await fs.promises.mkdir(path.join(skillRoot, "dup-b"), { recursive: true });
  await fs.promises.mkdir(path.join(skillRoot, "consumer"), { recursive: true });
  await fs.promises.mkdir(path.join(root, "tools", "aim"), { recursive: true });
  await fs.promises.writeFile(path.join(root, "tools", "aim", "README.md"), "existing repo tool\n");

  await fs.promises.writeFile(
    path.join(skillRoot, "target", "SKILL.md"),
    "---\nname: target-skill\ndescription: target\n---\n",
  );
  await fs.promises.writeFile(
    path.join(skillRoot, "dup-a", "SKILL.md"),
    "---\nname: dup-skill\ndescription: dup a\n---\n",
  );
  await fs.promises.writeFile(
    path.join(skillRoot, "dup-b", "SKILL.md"),
    "---\nname: dup-skill\ndescription: dup b\n---\n",
  );
  await fs.promises.writeFile(
    path.join(skillRoot, "consumer", "SKILL.md"),
    [
      "---",
      "name: consumer-skill",
      "description: consumer",
      "meta:",
      "  requires_skills: target-skill, dup-skill, missing-skill",
      "  requires_hooks: none",
      "  requires_repo_tools: tools/aim, does/not/exist",
      "---",
      "",
    ].join("\n"),
  );

  const registry = [{ id: "fixture", tool: "Fixture Tool", plugin: "fixture", root: "tool/plugin/skills" }];
  const output = path.join(root, "output");
  const result = await buildPublication({
    repoRoot: root,
    registry,
    generatedRoot: path.join(output, "generated"),
    downloadRoot: path.join(output, "downloads"),
    aiIndexPath: path.join(output, "ai-index.json"),
    searchIndexPath: path.join(output, "search-index.json"),
  });

  const consumer = result.catalog.skills.find((skill) => skill.name === "consumer-skill");
  assert.deepEqual(consumer.meta.requiresSkills, [
    { name: "target-skill", path: "tool/plugin/skills/target/SKILL.md" },
    { name: "dup-skill", path: null },
    { name: "missing-skill", path: null },
  ]);
  assert.equal(consumer.meta.requiresHooks, null);
  assert.deepEqual(consumer.meta.requiresRepoTools, [
    { text: "tools/aim", href: "https://github.com/fdshg693/AI/tree/main/tools/aim" },
    { text: "does/not/exist", href: null },
  ]);

  const target = result.catalog.skills.find((skill) => skill.name === "target-skill");
  assert.deepEqual(target.meta.requiresSkills, []);
  assert.equal(target.meta.requiresHooks, null);
});

test("wraps a set requires_hooks value into a single link to .claude/hooks", async () => {
  const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), "skill-site-test-"));
  const skillRoot = path.join(root, "tool", "plugin", "skills");
  await fs.promises.mkdir(path.join(skillRoot, "hooked"), { recursive: true });
  await fs.promises.writeFile(
    path.join(skillRoot, "hooked", "SKILL.md"),
    "---\nname: hooked-skill\ndescription: hooked\nmeta:\n  requires_hooks: 'PreToolUse: Bash差し戻し'\n---\n",
  );
  const registry = [{ id: "fixture", tool: "Fixture Tool", plugin: "fixture", root: "tool/plugin/skills" }];
  const output = path.join(root, "output");
  const result = await buildPublication({
    repoRoot: root,
    registry,
    generatedRoot: path.join(output, "generated"),
    downloadRoot: path.join(output, "downloads"),
    aiIndexPath: path.join(output, "ai-index.json"),
    searchIndexPath: path.join(output, "search-index.json"),
  });
  const hooked = result.catalog.skills.find((skill) => skill.name === "hooked-skill");
  assert.deepEqual(hooked.meta.requiresHooks, {
    text: "PreToolUse: Bash差し戻し",
    href: "https://github.com/fdshg693/AI/tree/main/.claude/hooks",
  });
});

test("validates generated catalog and archives", async () => {
  const fixture = await fixtureRepo();
  const output = path.join(fixture.root, "output");
  await buildPublication({
    repoRoot: fixture.root,
    registry: fixture.registry,
    generatedRoot: path.join(output, "generated"),
    downloadRoot: path.join(output, "downloads"),
    aiIndexPath: path.join(output, "ai-index.json"),
    searchIndexPath: path.join(output, "search-index.json"),
  });
  const result = await validatePublication({
    repoRoot: fixture.root,
    registry: fixture.registry,
    generatedRoot: path.join(output, "generated"),
    downloadRoot: path.join(output, "downloads"),
    aiIndexPath: path.join(output, "ai-index.json"),
    searchIndexPath: path.join(output, "search-index.json"),
  });
  assert.equal(result.count, 3);
});
