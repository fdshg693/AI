import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.resolve(SCRIPT_DIRECTORY, "..");

export const DEFAULT_INDEX_PATH = path.join(PACKAGE_ROOT, "data", "skill-index.json");

/** Read the local skill index, or null when missing/unreadable/invalid JSON. */
export async function readIndex(indexPath = DEFAULT_INDEX_PATH) {
  try {
    return JSON.parse(await fs.promises.readFile(indexPath, "utf8"));
  } catch {
    return null;
  }
}

export async function writeIndex(index, indexPath = DEFAULT_INDEX_PATH) {
  await fs.promises.mkdir(path.dirname(indexPath), { recursive: true });
  await fs.promises.writeFile(indexPath, `${JSON.stringify(index, null, 2)}\n`, "utf8");
}
