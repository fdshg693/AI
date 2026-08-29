import { readFileSync } from "node:fs";

/** Minimal .env loader (no external dependency). Real environment variables win. */
export function loadDotenv(envPath) {
  let text;
  try {
    text = readFileSync(envPath, "utf-8");
  } catch {
    return;
  }
  for (const raw of text.split(/\r?\n/)) {
    let line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    if (line.startsWith("export ")) line = line.slice(7).trim();
    const eq = line.indexOf("=");
    if (eq === -1) continue;
    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    if (
      value.length >= 2 &&
      value[0] === value[value.length - 1] &&
      "\"'".includes(value[0])
    ) {
      value = value.slice(1, -1);
    }
    if (key && !(key in process.env)) process.env[key] = value;
  }
}
