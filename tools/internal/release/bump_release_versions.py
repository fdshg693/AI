"""Bump pyproject.toml's version for repo-tools.yaml release:true tools.

For each tool folder registered with `release: true` in repo-tools.yaml,
checks whether any of the given (default: currently staged) files live under
that folder, and if so runs `uv version --bump patch --frozen` there. This is
folder-granular, not per-file: touching any file under a release tool's path
(docs included) bumps that tool's patch version exactly once, regardless of
how many files under it changed. `--frozen` limits the write to the version
field in pyproject.toml, without re-locking uv.lock.

The bumped pyproject.toml is `git add`-ed directly rather than left for
lefthook's `stage_fixed` to pick up: stage_fixed only re-stages files that
were already part of the job's own staged+glob-matched fileset, so a
docs-only change (e.g. only README.md staged) would otherwise leave the
bumped pyproject.toml as an untracked modification outside the commit.

repo-tools.yaml is parsed directly here rather than via
skill.util.repo_tools_registry.load_repo_tools, matching the precedent set by
.github/workflows/tool-release.yml's discover job (see
tools/internal/skill/AGENTS.md: that util module's consumers are limited to
skill/set and skill/check).

Run standalone via `just --justfile tools/internal/justfile
release-version-bump`, or let lefthook pass the staged file list.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
REPO_TOOLS_YAML_PATH = REPO_ROOT / "repo-tools.yaml"


def release_tool_paths() -> list[str]:
    data = yaml.safe_load(REPO_TOOLS_YAML_PATH.read_text(encoding="utf-8"))
    return [tool["path"] for tool in data["tools"].values() if tool.get("release")]


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def main(argv: list[str]) -> int:
    changed = argv[1:] if len(argv) > 1 else staged_files()
    changed_posix = [Path(p).as_posix() for p in changed]

    bumped = 0
    for tool_path in release_tool_paths():
        prefix = f"{tool_path}/"
        if not any(f.startswith(prefix) for f in changed_posix):
            continue

        result = subprocess.run(
            ["uv", "version", "--bump", "patch", "--frozen"],
            cwd=REPO_ROOT / tool_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(
                f"error: failed to bump version for {tool_path}:\n{result.stderr}",
                file=sys.stderr,
            )
            return 1

        add_result = subprocess.run(
            ["git", "add", "--", f"{tool_path}/pyproject.toml"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if add_result.returncode != 0:
            print(
                f"error: failed to stage {tool_path}/pyproject.toml:\n{add_result.stderr}",
                file=sys.stderr,
            )
            return 1

        print(f"{tool_path}: {result.stdout.strip()}")
        bumped += 1

    if bumped == 0:
        print("No release-target tool folders changed; nothing to bump.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
