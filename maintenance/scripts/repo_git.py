"""Git helpers that see the umbrella and its checked-out submodules as one tree.

The pre-commit tasks address files by umbrella-relative paths (``tools/aim/...``,
``skills/plugins/...``). After the submodule split those files live in separate
repositories, so ``git diff --cached`` / ``git show`` / ``git add`` must run in
the repository that owns the path. A commit made inside a submodule runs the
same tasks (via the submodule's ``lefthook.yml``), so staged files are gathered
from every repository and reported with the submodule path as prefix.

Submodules are read from ``.gitmodules`` directly (no ``git config`` call), and a
submodule that is not checked out is skipped.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath

_PATH_LINE_RE = re.compile(r"^\s*path\s*=\s*(.+?)\s*$")


def submodule_paths(root: Path) -> list[str]:
    """Posix paths (umbrella-relative) of checked-out submodules, longest first."""
    gitmodules = root / ".gitmodules"
    if not gitmodules.is_file():
        return []
    paths: list[str] = []
    for line in gitmodules.read_text(encoding="utf-8").splitlines():
        match = _PATH_LINE_RE.match(line)
        if match is None:
            continue
        rel = PurePosixPath(match.group(1)).as_posix()
        if (root / rel / ".git").exists():
            paths.append(rel)
    return sorted(paths, key=len, reverse=True)


def owner(root: Path, rel_posix: str) -> tuple[Path, str]:
    """Return (repository directory, path inside it) for an umbrella-relative path."""
    for sub in submodule_paths(root):
        if rel_posix.startswith(f"{sub}/"):
            return root / sub, rel_posix[len(sub) + 1 :]
    return root, rel_posix


def _staged_in(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return [line for line in result.stdout.splitlines() if line.strip()]


def staged_files(root: Path) -> list[str]:
    """Staged (ACMR) paths of the umbrella and every checked-out submodule.

    Submodule paths are prefixed with the submodule's path. The umbrella's own
    gitlink entries (e.g. ``skills`` after a pointer update) are kept as-is so
    tasks can glob on them.
    """
    paths = _staged_in(root)
    for sub in submodule_paths(root):
        paths.extend(f"{sub}/{path}" for path in _staged_in(root / sub))
    return paths


def show(root: Path, rev: str, rel_posix: str) -> str | None:
    """``git show <rev>:<path>`` in the repository owning the path, or None."""
    repo, inner = owner(root, rel_posix)
    result = subprocess.run(
        ["git", "show", f"{rev}:{inner}"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def add(root: Path, rel_posix: str) -> subprocess.CompletedProcess[str]:
    """``git add -- <path>`` in the repository owning the path."""
    repo, inner = owner(root, rel_posix)
    return subprocess.run(
        ["git", "add", "--", inner],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
