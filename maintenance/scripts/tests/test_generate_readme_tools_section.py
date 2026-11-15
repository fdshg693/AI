from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugin_meta.generate import generate_readme_tools_section as gen  # noqa: E402


def tool(*entries: dict) -> dict:
    return {"readme": {"config_dirs": list(entries)}}


def test_link_defaults_to_markdown_link() -> None:
    lines = gen.build_tool_block("cline", tool({"path": ".cline", "description": "d"}))
    assert lines == ["- **Cline**", "  - [.cline/](.cline/) — d"]


def test_link_true_is_markdown_link() -> None:
    lines = gen.build_tool_block(
        "cline", tool({"path": ".cline", "description": "d", "link": True})
    )
    assert lines[1] == "  - [.cline/](.cline/) — d"


def test_link_false_is_code_span() -> None:
    lines = gen.build_tool_block(
        "antigravity", tool({"path": ".agents/rules", "description": "d", "link": False})
    )
    assert lines == ["- **Antigravity**", "  - `.agents/rules/` — d"]


def test_non_bool_link_exits() -> None:
    with pytest.raises(SystemExit):
        gen.build_tool_block(
            "cline", tool({"path": ".clinerules", "description": "d", "link": "false"})
        )
