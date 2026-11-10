"""Regenerate .github/plugin/marketplace.json from the copilot marketplace
sources listed in ai-tools.yaml.

Each ``marketplace.sources`` entry is a plugin dir whose root ``plugin.json``
(the Copilot / Agent Plugins manifest) is maintained with the plugin itself;
this script only reads it. Marketplace-level fields (name, owner, metadata)
come from ai-tools.yaml. The output is fully regenerated (not merged) on each
run. Plugins inside a submodule get a ``github`` source (repo + path) pointing
at the submodule's repository.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from plugin_meta.util.ai_tools_config import REPO_ROOT, load_tool
from plugin_meta.util.plugin_source import remote_plugin

TOOL_KEY = "copilot"


def copilot_source(rel_posix: str) -> str | dict:
    remote = remote_plugin(REPO_ROOT, rel_posix)
    if remote is not None:
        # Inside a submodule: fetch from the submodule's repository.
        return {"source": "github", "repo": remote.repo, "path": remote.path}
    return f"./{rel_posix}"


def plugin_entry(source: str) -> dict:
    manifest_path = REPO_ROOT / source / "plugin.json"
    if not manifest_path.is_file():
        sys.exit(f"error: {manifest_path.relative_to(REPO_ROOT).as_posix()} not found")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = {
        "name": manifest["name"],
        "description": manifest.get("description", ""),
        "version": manifest.get("version", "1.0.0"),
        "source": copilot_source(Path(source).as_posix()),
    }
    if "repository" in manifest:
        entry["repository"] = manifest["repository"]
    return entry


def build_marketplace(marketplace_config: dict) -> dict:
    return {
        "name": marketplace_config["name"],
        "owner": marketplace_config["owner"],
        "metadata": marketplace_config["metadata"],
        "plugins": [plugin_entry(source) for source in marketplace_config["sources"]],
    }


def main() -> None:
    marketplace_config = load_tool(TOOL_KEY)["marketplace"]
    marketplace_path = REPO_ROOT / marketplace_config["output_path"]
    marketplace = build_marketplace(marketplace_config)
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)
    marketplace_path.write_text(
        json.dumps(marketplace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Wrote {len(marketplace['plugins'])} plugins to {marketplace_path}")


if __name__ == "__main__":
    main()
