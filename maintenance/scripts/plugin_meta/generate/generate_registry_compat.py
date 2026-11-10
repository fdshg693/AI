"""Regenerate root-level compatibility copies of the registry/ files skill-tools reads.

The SSOT yaml files live under registry/. skill-tools releases from before that
move read ai-tools.yaml, repo-tools.yaml, repo-workflows.yaml and repo-hooks.yaml
from the source root by fixed name, so a GitHub source pinned to main would
break for them. Each root copy is the registry file verbatim behind a
"do not edit" header; paths inside stay repository-root relative, so the copy
means the same thing in either place. Current skill-tools prefers registry/.

Remove this generator (and the root copies) once old skill-tools installs no
longer need to be supported.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_DIR = REPO_ROOT / "registry"
COMPAT_FILES = ("ai-tools.yaml", "repo-tools.yaml", "repo-workflows.yaml", "repo-hooks.yaml")
HEADER = (
    "# GENERATED compatibility copy of registry/{name} (DO NOT EDIT MANUALLY).\n"
    "# Edit registry/{name}; maintenance/scripts/plugin_meta/generate/\n"
    "# generate_registry_compat.py rewrites this file for skill-tools releases\n"
    "# that still read SSOT files from the repository root.\n"
)


def render(name: str) -> str:
    body = (REGISTRY_DIR / name).read_text(encoding="utf-8")
    return HEADER.format(name=name) + body


def main() -> int:
    for name in COMPAT_FILES:
        target = REPO_ROOT / name
        content = render(name)
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != content:
            target.write_bytes(content.encode("utf-8"))
            print(f"Wrote {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
