#!/usr/bin/env node
import { parseArgs } from "node:util";
import { loadLocalEnv } from "../../../skills-site/scripts/build-skill-embeddings.mjs";
import { buildIndex } from "./build-index.mjs";
import { writeIndex, DEFAULT_INDEX_PATH } from "./index-store.mjs";
import { searchSkills } from "./search.mjs";

async function runBuildIndex() {
  loadLocalEnv();
  const { index, warnings } = await buildIndex();
  await writeIndex(index);
  for (const warning of warnings) console.warn(`warning: ${warning}`);
  console.log(`Wrote ${index.skills.length} skills to ${DEFAULT_INDEX_PATH} (embeddingModel: ${index.embeddingModel})`);
}

function printTable(results) {
  if (results.length === 0) {
    console.log("(no results)");
    return;
  }
  console.log(["score", "path", "name"].join("\t"));
  for (const { path, name, score } of results) {
    console.log([score.toFixed(4), path, name].join("\t"));
  }
}

async function runSearch(rawArgs) {
  const { values } = parseArgs({
    args: rawArgs,
    options: {
      query: { type: "string", short: "q" },
      top: { type: "string", short: "k", default: "10" },
      json: { type: "boolean", default: false },
    },
  });
  if (!values.query) {
    throw new Error("Usage: skill-search search --query <text> [--top <n>] [--json]");
  }

  loadLocalEnv();
  const results = await searchSkills(values.query, { topK: Number(values.top) });

  if (values.json) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    printTable(results);
  }
}

async function main() {
  const [subcommand, ...rest] = process.argv.slice(2);

  switch (subcommand) {
    case "build-index":
      await runBuildIndex();
      break;
    case "search":
      await runSearch(rest);
      break;
    default:
      console.error(`Unknown subcommand: ${subcommand ?? "(none)"}\nUsage: skill-search <build-index|search>`);
      process.exitCode = 1;
  }
}

try {
  await main();
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
