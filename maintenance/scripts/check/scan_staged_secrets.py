"""Scan currently staged files with secretlint, in argv-safe batches.

lefthook's ``{staged_files}`` substitution hits Windows CreateProcess limits
on large commits. This script reads staged paths from git and invokes
secretlint in chunks. Wired via lefthook; run
``just --justfile maintenance/scripts/justfile scan-staged-secrets``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import repo_git

REPO_ROOT = Path(__file__).resolve().parents[3]
# cmd.exe is ~8191 chars; leave room for ``pnpm exec secretlint ...``.
_MAX_BATCH_CHARS = 4000
_SECRETLINT = [
    "pnpm",
    "exec",
    "secretlint",
    "--secretlintrc",
    ".secretlintrc.json",
]


def staged_files() -> list[str]:
    try:
        return repo_git.staged_files(REPO_ROOT)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc


def batched(paths: list[str], *, max_chars: int = _MAX_BATCH_CHARS) -> list[list[str]]:
    batches: list[list[str]] = []
    current: list[str] = []
    size = 0
    for path in paths:
        extra = len(path) + 1
        if current and size + extra > max_chars:
            batches.append(current)
            current = []
            size = 0
        current.append(path)
        size += extra
    if current:
        batches.append(current)
    return batches


def main() -> int:
    paths = staged_files()
    if not paths:
        return 0
    for batch in batched(paths):
        result = subprocess.run([*_SECRETLINT, *batch], cwd=REPO_ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
