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

import os
import re
import subprocess
from pathlib import Path, PurePosixPath

_PATH_LINE_RE = re.compile(r"^\s*path\s*=\s*(.+?)\s*$")

# Repository-local variables a git hook exports (``git rev-parse --local-env-vars``).
# They describe the repository whose hook is running (e.g. GIT_INDEX_FILE=.git/index,
# relative), so a git command run in another repository (umbrella <-> submodule)
# must not inherit them.
_LOCAL_GIT_ENV = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_DIR",
    "GIT_GRAFT_FILE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_REPLACE_REF_BASE",
    "GIT_SHALLOW_FILE",
    "GIT_WORK_TREE",
)


def _git_dir(repo: Path) -> Path | None:
    clean = {k: v for k, v in os.environ.items() if k not in _LOCAL_GIT_ENV}
    result = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=repo,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def _env_for(repo: Path) -> dict[str, str] | None:
    """Environment for git in ``repo``.

    Inherited (None) when no hook index is set or it belongs to ``repo`` (keeps a
    temporary index such as ``git commit -a`` uses); otherwise the hook-local
    variables are dropped so the command sees ``repo``'s own index.
    """
    index = os.environ.get("GIT_INDEX_FILE")
    if not index:
        return None
    index_path = Path(index)
    if not index_path.is_absolute():
        index_path = repo / index_path
    git_dir = _git_dir(repo)
    if git_dir is not None and index_path.resolve().parent == git_dir:
        return None
    return {k: v for k, v in os.environ.items() if k not in _LOCAL_GIT_ENV}


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


def _staged_in(repo: Path, *, include_deleted: bool = False) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--cached",
            "--no-renames",
            f"--diff-filter={'ACDMR' if include_deleted else 'ACMR'}",
        ],
        cwd=repo,
        env=_env_for(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return [line for line in result.stdout.splitlines() if line.strip()]


def staged_files(root: Path, *, include_deleted: bool = False) -> list[str]:
    """Staged paths of the umbrella and every checked-out submodule.

    Submodule paths are prefixed with the submodule's path. The umbrella's own
    gitlink entries (e.g. ``skills`` after a pointer update) are kept as-is so
    tasks can glob on them.
    """
    paths = _staged_in(root, include_deleted=include_deleted)
    for sub in submodule_paths(root):
        paths.extend(
            f"{sub}/{path}" for path in _staged_in(root / sub, include_deleted=include_deleted)
        )
    return paths


def _tracked_in(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        env=_env_for(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return [path for path in result.stdout.split("\0") if path]


def tracked_files(root: Path) -> list[str]:
    """Index entries (``git ls-files``) of the umbrella and every checked-out submodule.

    Paths are umbrella-relative; submodule entries carry the submodule path as
    prefix. The umbrella's gitlinks (``skills`` etc.) are listed as-is.
    """
    paths = _tracked_in(root)
    for sub in submodule_paths(root):
        paths.extend(f"{sub}/{path}" for path in _tracked_in(root / sub))
    return paths


def ignored_files(root: Path, rel_paths: list[str]) -> set[str]:
    """Subset of umbrella-relative ``rel_paths`` that the owning repository ignores.

    Uses ``git check-ignore --no-index`` so a tracked file is still reported when
    a pattern matches it. One call per owning repository.
    """
    by_repo: dict[Path, list[tuple[str, str]]] = {}
    for rel in rel_paths:
        repo, inner = owner(root, rel)
        by_repo.setdefault(repo, []).append((rel, inner))
    ignored: set[str] = set()
    for repo, pairs in by_repo.items():
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--stdin", "-z"],
            cwd=repo,
            env=_env_for(repo),
            input="".join(f"{inner}\0" for _, inner in pairs),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        # 0: some paths ignored, 1: none ignored, anything else: error.
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        hits = {path for path in result.stdout.split("\0") if path}
        ignored.update(rel for rel, inner in pairs if inner in hits)
    return ignored


def show(root: Path, rev: str, rel_posix: str) -> str | None:
    """``git show <rev>:<path>`` in the repository owning the path, or None."""
    repo, inner = owner(root, rel_posix)
    result = subprocess.run(
        ["git", "show", f"{rev}:{inner}"],
        cwd=repo,
        env=_env_for(repo),
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
        env=_env_for(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def submodule_urls(root: Path) -> dict[str, str]:
    """Posix path -> url for every submodule in ``.gitmodules`` (checked out or not)."""
    gitmodules = root / ".gitmodules"
    if not gitmodules.is_file():
        return {}
    result: dict[str, str] = {}
    path: str | None = None
    url: str | None = None
    for line in [*gitmodules.read_text(encoding="utf-8").splitlines(), "["]:
        stripped = line.strip()
        if stripped.startswith("["):
            if path and url:
                result[path] = url
            path = url = None
            continue
        key, sep, value = stripped.partition("=")
        if not sep:
            continue
        if key.strip() == "path":
            path = PurePosixPath(value.strip()).as_posix()
        elif key.strip() == "url":
            url = value.strip()
    return result
