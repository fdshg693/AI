"""Generate GitHub Copilot path-specific instructions from AGENTS.md files.

Each AGENTS.md is copied to
.github/instructions/<directory>.instructions.md and receives frontmatter
with an applyTo entry for the directory containing the source file. The
repository-root AGENTS.md is written as root.instructions.md and uses the
catch-all pattern **.
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
    """Build the Copilot glob for files governed by an AGENTS.md."""

    directory = relative_directory(agent_path, repo_root).as_posix()
    return "**" if directory == "." else f"{directory}/**"


def output_path(agent_path: Path, repo_root: Path, output_dir: Path) -> Path:
    """Return the generated instruction path for an AGENTS.md."""

    directory = relative_directory(agent_path, repo_root)
    relative_name = "root" if directory == Path(".") else "-".join(directory.parts)
    return output_dir / f"{relative_name}.instructions.md"


def instruction_name(agent_path: Path, repo_root: Path) -> str:
    """Return a stable human-readable name for a generated instruction."""

    directory = relative_directory(agent_path, repo_root)
    if directory == Path("."):
        return "Repository instructions"
    return f"{directory.as_posix()} instructions"


def instruction_description(agent_path: Path, repo_root: Path) -> str:
    """Return a description of the instruction's path scope."""

    directory = relative_directory(agent_path, repo_root)
    scope = "the repository" if directory == Path(".") else f"{directory.as_posix()}/"
    return f"Instructions for files in {scope}"


def render_instruction(agent_path: Path, repo_root: Path) -> str:
    """Render one Copilot instruction while preserving the AGENTS.md body."""

    name = json.dumps(instruction_name(agent_path, repo_root), ensure_ascii=False)
    description = json.dumps(instruction_description(agent_path, repo_root), ensure_ascii=False)
    apply_to = json.dumps(path_pattern(agent_path, repo_root), ensure_ascii=False)
    body = agent_path.read_text(encoding="utf-8").rstrip("\n")
    return f"---\nname: {name}\ndescription: {description}\napplyTo: {apply_to}\n---\n\n{body}\n"


def generate(repo_root: Path, output_dir: Path) -> int:
    """Generate instructions and return the number of source files processed."""

    agents = discover_agents(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    for agent_path in agents:
        target_path = output_path(agent_path, repo_root, output_dir)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            render_instruction(agent_path, repo_root),
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
        description="Generate GitHub Copilot instructions from repository AGENTS.md files."
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
        help="Generated instruction directory (default: ai-tools.yaml's copilot.instructions_from_agents_md.output_dir)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    default_output_dir = (
        repo_root / load_tool("copilot")["instructions_from_agents_md"]["output_dir"]
    )
    output_dir = args.output_dir or default_output_dir
    output_dir = output_dir.resolve()
    count = generate(repo_root, output_dir)
    print(f"Generated {count} GitHub Copilot instructions in {output_dir}")


if __name__ == "__main__":
    main()
