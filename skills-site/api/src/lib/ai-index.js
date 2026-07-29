import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DATA_ROOT = path.resolve(HERE, "../../data");

let cachedAiIndex = null;

export function loadAiIndex() {
  if (cachedAiIndex) return cachedAiIndex;
  const raw = fs.readFileSync(path.join(DATA_ROOT, "ai-index.json"), "utf8");
  const parsed = JSON.parse(raw);
  if (!parsed || !Array.isArray(parsed.skills)) {
    throw new Error("ai-index.json has unexpected shape");
  }
  cachedAiIndex = parsed;
  return cachedAiIndex;
}
