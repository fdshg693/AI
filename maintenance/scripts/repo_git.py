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


# Set by git for hooks; they pin every git call to the committing repository.
_REPO_ENV_VARS = (
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_WORK_TREE",
    "GIT_PREFIX",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
)


def _git_dir_of(repo: Path) -> Path | None:
    dot_git = repo / ".git"
    if dot_git.is_dir():
        return dot_git.resolve()
    if dot_git.is_file():
        text = dot_git.read_text(encoding="utf-8", errors="replace").strip()
        if text.startswith("gitdir:"):
            return (repo / text[len("gitdir:") :].strip()).resolve()
    return None


def _git_env(repo: Path) -> dict[str, str] | None:
    """Environment for a git call in ``repo``.

    A hook of a commit made inside a submodule inherits ``GIT_DIR`` /
    ``GIT_INDEX_FILE`` pointing at that submodule, so ``git diff --cached`` run
    in the umbrella (or another submodule) would read the committing
    submodule's index. Keep them only for the repository they belong to (its
    index may be a temporary one, e.g. ``git commit -a``); drop them elsewhere.
    Returns None (inherit unchanged) when nothing needs dropping.
    """
    hook_git_dir = os.environ.get("GIT_DIR")
    if not hook_git_dir:
        return None
    if _git_dir_of(repo) == Path(hook_git_dir).resolve():
        return None
    env = dict(os.environ)
    for key in _REPO_ENV_VARS:
        env.pop(key, None)
    return env


def _env_kwargs(repo: Path) -> dict[str, dict[str, str]]:
    env = _git_env(repo)
    return {} if env is None else {"env": env}


def _staged_in(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
        cwd=repo,
        **_env_kwargs(repo),
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
        **_env_kwargs(repo),
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
        **_env_kwargs(repo),
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
