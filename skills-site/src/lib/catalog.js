import catalog from "../../generated/catalog.json";

export const skills = catalog.skills;

// meta_field.yaml (repo root) is the SSOT for these entries; build-catalog.mjs
// loads it once via meta-field-registry.mjs and embeds it here so UI code
// never reads meta_field.yaml itself (Astro/Vite relocates bundled modules
// during prerendering, which breaks meta-field-registry.mjs's file-relative
// path resolution if imported directly from a component).
export const metaFieldRegistry = catalog.metaFieldRegistry;

export function metaFieldDefault(field) {
  return metaFieldRegistry.find((entry) => entry.field === field)?.default;
}

export function sortedUnique(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b, "ja"));
}

export function skillHref(path) {
  return sitePath(
    ["skills", ...path.split("/").map((segment) => encodeURIComponent(segment))].join("/"),
  );
}

export function downloadHref(download) {
  return sitePath(download.split("/").map((segment) => encodeURIComponent(segment)).join("/"));
}

export function sitePath(path = "") {
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  const suffix = path ? `/${path.replace(/^\//, "")}` : "";
  return `${base}${suffix || "/"}`;
}
