import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  DEFAULT_MODEL,
  MODEL_STORAGE,
  apiErrorMessage,
  skillHref,
} from "../src/lib/ai-suggest.mjs";
import {
  buildMessages,
  extractText,
  matchSuggestions,
  parseSuggestions,
} from "../api/src/lib/suggest-core.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const aiSuggestAstro = fs.readFileSync(path.join(here, "..", "src", "components", "AISuggest.astro"), "utf8");
const aiSuggestReact = fs.readFileSync(
  path.join(here, "..", "src", "components", "react", "AISuggest.tsx"),
  "utf8",
);

const AI_INDEX = {
  schemaVersion: 1,
  skills: [
    { path: "tool/plugin/skills/a/SKILL.md", name: "skill-a", description: "desc a", tool: "Claude Code", plugin: "meta" },
  ],
};

test("skillHref mirrors catalog segment-encoding", () => {
  assert.equal(skillHref("tool/plugin/skills/a/SKILL.md"), "/skills/tool/plugin/skills/a/SKILL.md");
  assert.equal(
    skillHref("tool/my plugin/skills/a/SKILL.md", "/base"),
    "/base/skills/tool/my%20plugin/skills/a/SKILL.md",
  );
});

test("parseSuggestions accepts bare JSON and fenced JSON", () => {
  const payload = [{ path: "a", reason: "r" }];
  assert.deepEqual(parseSuggestions(JSON.stringify(payload)), payload);
  assert.deepEqual(parseSuggestions("```json\n" + JSON.stringify(payload) + "\n```"), payload);
});

test("matchSuggestions keeps only paths present in the index", () => {
  const matched = matchSuggestions(
    [
      { path: "tool/plugin/skills/a/SKILL.md", reason: "関連するため" },
      { path: "tool/plugin/skills/does-not-exist/SKILL.md", reason: "捏造されたパス" },
    ],
    AI_INDEX.skills,
  );
  assert.equal(matched.length, 1);
  assert.equal(matched[0].skill.name, "skill-a");
  assert.equal(matched[0].reason, "関連するため");
});

test("buildMessages embeds the catalog and asks for JSON-only output", () => {
  const messages = buildMessages("テストについて", AI_INDEX.skills);
  assert.equal(messages.length, 2);
  assert.match(messages[0].content, /JSON配列のみ/);
  assert.match(messages[1].content, /スキル一覧:/);
  assert.match(messages[1].content, /質問: テストについて/);
});

test("extractText flattens string and multipart content", () => {
  assert.equal(extractText("hello"), "hello");
  assert.equal(extractText([{ text: "a" }, "b", { text: "c" }]), "abc");
});

test("apiErrorMessage maps server error codes", () => {
  assert.match(apiErrorMessage("rate_limited", 429), /レート制限/);
  assert.match(apiErrorMessage("timeout", 504), /タイムアウト/);
  assert.match(apiErrorMessage("unavailable", 503), /利用できません/);
});

test("model storage constant stays stable", () => {
  assert.equal(MODEL_STORAGE, "skills-site:openrouter-model");
  assert.equal(DEFAULT_MODEL, "minimax/minimax-m3");
});

test("AISuggest.astro mounts the React island with client:load and no BYOK props", () => {
  assert.match(aiSuggestAstro, /import AISuggestReact from "\.\/react\/AISuggest"/);
  assert.match(aiSuggestAstro, /client:load/);
  assert.match(aiSuggestAstro, /apiHref="\/api\/suggest"/);
  assert.doesNotMatch(aiSuggestAstro, /ai-index\.json/);
  assert.doesNotMatch(aiSuggestAstro, /ai-suggest\.js/);
});

test("AISuggest React component calls /api/suggest and has no API key UI", () => {
  assert.match(aiSuggestReact, /data-ai-submit/);
  assert.match(aiSuggestReact, /\/api\/suggest|apiHref/);
  assert.doesNotMatch(aiSuggestReact, /data-ai-key-save/);
  assert.doesNotMatch(aiSuggestReact, /data-ai-key-verify/);
  assert.doesNotMatch(aiSuggestReact, /KEY_STORAGE/);
  assert.doesNotMatch(aiSuggestReact, /OPENROUTER_URL/);
  assert.doesNotMatch(aiSuggestReact, /localStorage\.setItem\(KEY_STORAGE/);
});

test("public ai-suggest.js is removed after server migration", () => {
  assert.equal(fs.existsSync(path.join(here, "..", "public", "ai-suggest.js")), false);
});
