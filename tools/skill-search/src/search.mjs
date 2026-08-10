import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { cosineSimilarity } from "../../../skills-site/api/src/lib/embedding-similarity.js";
import { fetchEmbeddings } from "../../../skills-site/api/src/lib/embeddings.js";
import { readIndex } from "./index-store.mjs";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(SCRIPT_DIRECTORY, "..", "..", "..");

/**
 * Search the local skill index (built via `build-index`) by cosine similarity
 * to `query`. Skills whose SKILL.md no longer exists on disk are excluded
 * before ranking, so a stale index never surfaces a dead result.
 *
 * @param {string} query
 * @param {{ topK?: number, indexPath?: string, repoRoot?: string, apiKey?: string }} [options]
 * @returns {Promise<Array<{ path: string, name: string, description: string, tool: string, plugin: string, status: { key: string }, score: number }>>}
 */
export async function searchSkills(
  query,
  { topK = 10, indexPath, repoRoot = REPO_ROOT, apiKey = process.env.OPENROUTER_API_KEY?.trim() } = {},
) {
  const index = await readIndex(indexPath);
  if (!index) {
    throw new Error("Local skill index not found. Run `skill-search build-index` first.");
  }

  const liveSkills = index.skills.filter((skill) => fs.existsSync(path.join(repoRoot, skill.path)));

  const [queryEmbedding] = await fetchEmbeddings([query], { apiKey });

  const scored = [];
  for (const skill of liveSkills) {
    const score = cosineSimilarity(queryEmbedding, skill.embedding);
    if (!Number.isFinite(score)) continue;
    scored.push({
      path: skill.path,
      name: skill.name,
      description: skill.description,
      tool: skill.tool,
      plugin: skill.plugin,
      status: skill.status,
      score,
    });
  }
  scored.sort((left, right) => right.score - left.score || left.path.localeCompare(right.path));
  return scored.slice(0, topK);
}
