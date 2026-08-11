import path from "node:path";
import { fileURLToPath } from "node:url";
import { discoverSkills } from "../../../skills-site/scripts/publication-core.mjs";
import { SOURCE_REGISTRY } from "../../../skills-site/scripts/source-registry.mjs";
import { SITE_OVERRIDES } from "../../../skills-site/scripts/site-overrides.mjs";
import {
  EMBEDDING_DIMENSIONS,
  EMBEDDING_MODEL,
  attachSkillEmbeddings,
} from "../../../skills-site/scripts/build-skill-embeddings.mjs";
import { readIndex } from "./index-store.mjs";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(SCRIPT_DIRECTORY, "..", "..", "..");

// Independent from skills-site's AI_INDEX_SCHEMA_VERSION (skills-site/scripts/build-skill-embeddings.mjs):
// this is a separate artifact with its own schema evolution.
export const SKILL_INDEX_SCHEMA_VERSION = 1;

function isReusablePreviousIndex(previous) {
  return Boolean(
    previous &&
      previous.schemaVersion === SKILL_INDEX_SCHEMA_VERSION &&
      previous.embeddingModel === EMBEDDING_MODEL &&
      previous.embeddingDimensions === EMBEDDING_DIMENSIONS &&
      Array.isArray(previous.skills),
  );
}

/**
 * Discover skills, attach embeddings (reusing previous vectors by content
 * hash where possible), and return the index to write plus any discovery
 * warnings. Does not write to disk — callers use index-store.mjs for that.
 */
export async function buildIndex({
  repoRoot = REPO_ROOT,
  registry = SOURCE_REGISTRY,
  overrides = SITE_OVERRIDES,
  attachEmbeddings = attachSkillEmbeddings,
  loadPreviousIndex = readIndex,
} = {}) {
  const { skills, warnings } = await discoverSkills({ repoRoot, registry, overrides });
  const slimSkills = skills.map((skill) => ({
    path: skill.path,
    name: skill.name,
    description: skill.description,
    tool: skill.tool,
    plugin: skill.plugin,
    status: { key: skill.status.key },
  }));

  const previous = await loadPreviousIndex();
  const previousIndex = isReusablePreviousIndex(previous) ? previous : null;
  const skillsWithEmbeddings = await attachEmbeddings(slimSkills, { previousIndex });

  const index = {
    schemaVersion: SKILL_INDEX_SCHEMA_VERSION,
    embeddingModel: EMBEDDING_MODEL,
    embeddingDimensions: EMBEDDING_DIMENSIONS,
    skills: skillsWithEmbeddings,
  };
  return { index, warnings };
}
