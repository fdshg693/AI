"""Shared loader for repo-tools.yaml, the SSOT for tools/-installed CLI tools
that SKILL.md meta.requires_repo_tools / meta.requires_install declare.

Scripts that need this mapping (skill_meta_field_fill.py's classification
prompt, check_skill_repo_tools.py) must read through this module instead of
hardcoding tool names/paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
REPO_TOOLS_YAML_PATH = REPO_ROOT / "repo-tools.yaml"


def load_repo_tools(path: Path = REPO_TOOLS_YAML_PATH) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"repo-tools.yaml not found at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "tools" not in data:
        raise ValueError(f"{path} is missing a top-level 'tools' key")
    return data["tools"]
