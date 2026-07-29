"""Generate Cline conditional rules from repository AGENTS.md files.

Each AGENTS.md is copied to .clinerules/agents-<directory>.md and receives a
paths frontmatter entry for the directory containing the source file. The
repository-root AGENTS.md is written as .clinerules/agents-root.md and uses
the catch-all pattern **.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from plugin_meta.util.ai_tools_config import load_tool

REPO_ROOT = Path(__file__).resolve().parents[4]
IGNORED_DIR_NAMES = {".git", "node_modules", ".venv", "__pycache__"}


def discover_agents(repo_root: Path) -> list[Path]:
    """Return repository AGENTS.md files in deterministic order."""

    agents: list[Path] = []
    for current_dir, dir_names, file_names in os.walk(repo_root):
        dir_names[:] = sorted(name for name in dir_names if name not in IGNORED_DIR_NAMES)
        if "AGENTS.md" in file_names:
            agents.append(Path(current_dir) / "AGENTS.md")
    return sorted(agents, key=lambda path: path.relative_to(repo_root).as_posix())


def relative_directory(agent_path: Path, repo_root: Path) -> Path:
    """Return the directory containing an AGENTS.md, relative to repo_root."""

    directory = agent_path.parent.relative_to(repo_root)
    return Path() if directory == Path(".") else directory


def path_pattern(agent_path: Path, repo_root: Path) -> str:
    """Build the Cline glob for files governed by an AGENTS.md."""

    directory = relative_directory(agent_path, repo_root).as_posix()
    return "**" if directory == "." else f"{directory}/**"


def output_path(agent_path: Path, repo_root: Path, output_dir: Path) -> Path:
    """Return the generated rule path for an AGENTS.md."""

    directory = relative_directory(agent_path, repo_root)
    relative_name = "root" if directory == Path(".") else "-".join(directory.parts)
    return output_dir / f"{relative_name}.md"


def render_rule(agent_path: Path, repo_root: Path) -> str:
    """Render one Cline rule while preserving the AGENTS.md body."""

    pattern = json.dumps(path_pattern(agent_path, repo_root), ensure_ascii=False)
    body = agent_path.read_text(encoding="utf-8").rstrip("\n")
    return f"---\npaths:\n  - {pattern}\n---\n\n{body}\n"


def generate(repo_root: Path, output_dir: Path) -> int:
    """Generate rules and return the number of source files processed."""

    agents = discover_agents(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    for agent_path in agents:
        target_path = output_path(agent_path, repo_root, output_dir)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            render_rule(agent_path, repo_root),
            encoding="utf-8",
            newline="\n",
        )
        print(
            f"Generated {target_path.relative_to(repo_root)} "
            f"from {agent_path.relative_to(repo_root)}"
        )

    return len(agents)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Cline rules from repository AGENTS.md files."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to scan (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Generated rule directory (default: ai-tools.yaml's cline.rules_from_agents_md.output_dir)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    default_output_dir = repo_root / load_tool("cline")["rules_from_agents_md"]["output_dir"]
    output_dir = args.output_dir or default_output_dir
    output_dir = output_dir.resolve()
    count = generate(repo_root, output_dir)
    print(f"Generated {count} Cline rules in {output_dir}")


if __name__ == "__main__":
    main()
