"""Validate the plugin index against the indexes of both repositories."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import repo_git
from plugin_meta.generate.generate_skills_plugin_index import render
from plugin_meta.util.ai_tools_config import REPO_ROOT, load_tool


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=repo_git._env_for(repo),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def validate(root: Path, repository: str) -> None:
    skills = root / "skills"
    repo = skills if repository == "skills" else root
    staged = repo_git._staged_in(repo, include_deleted=True)
    relevant = (
        (lambda p: p == "README.md" or p.startswith("plugins/"))
        if repository == "skills"
        else (lambda p: p in ("skills", "registry/ai-tools.yaml"))
    )
    if not any(relevant(path) for path in staged):
        return

    # Both inputs must match their indexes, including additions and deletions.
    for directory, paths in (
        (root, ("registry/ai-tools.yaml",)),
        (skills, ("README.md", "plugins")),
    ):
        diff = git(directory, "diff", "--quiet", "--", *paths)
        untracked = git(directory, "ls-files", "--others", "--exclude-standard", "--", *paths)
        if diff.returncode != 0 or untracked.returncode != 0 or untracked.stdout:
            raise ValueError(
                f"unstaged or untracked index inputs in {directory}; stage them before checking"
            )

    if repository == "umbrella":
        pointer = git(root, "rev-parse", ":skills")
        head = git(skills, "rev-parse", "HEAD")
        clean = git(skills, "diff", "--cached", "--quiet", "HEAD", "--", "README.md", "plugins")
        if (
            pointer.returncode
            or head.returncode
            or pointer.stdout != head.stdout
            or clean.returncode
        ):
            raise ValueError(
                "commit skills README and plugin changes first, then stage the skills gitlink"
            )

    output, expected = render(root, load_tool("claude-code", root / "registry/ai-tools.yaml"))
    indexed = repo_git.show(root, "", output.relative_to(root).as_posix())
    if indexed != expected:
        raise ValueError("skills/README.md index is stale; regenerate and stage it in skills")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", choices=("submodule", "umbrella"))
    args = parser.parse_args()
    try:
        if (
            args.repository == "submodule"
            and Path.cwd().resolve() != (REPO_ROOT / "skills").resolve()
        ):
            return 0
        validate(REPO_ROOT, "skills" if args.repository == "submodule" else "umbrella")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"skills plugin index: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
