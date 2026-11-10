"""Branch operations that treat the umbrella and its submodules as one working set.

A branch in the umbrella does not create, switch or delete anything in a
submodule: the umbrella records only a commit pointer per submodule. Working on
two machines therefore needs the same branch name in every repository touched.
These commands do that in one step.

Every command that changes state checks all repositories first and changes
nothing if any check fails, so a refusal never leaves the set half switched.
Order follows the two-step commit: pushes go to submodules before the umbrella
(the umbrella must never point at an unpushed commit); pulls go to the umbrella
first.

Submodules are taken from ``.gitmodules`` (only checked-out ones). The
umbrella's ``git switch`` does not touch submodule working trees (no
``submodule.recurse``), so switching each repository explicitly is safe.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from repo_git import submodule_paths

REMOTE = "origin"
UMBRELLA_LABEL = "(umbrella)"
ALWAYS_PROTECTED = frozenset({"main", "master"})


class BranchError(Exception):
    """A pre-check failed; nothing was changed."""


@dataclass(frozen=True)
class Repo:
    label: str
    path: Path
    is_umbrella: bool


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, detail)
    return result


def find_root(start: Path) -> Path:
    """Umbrella root: the superproject when run inside a submodule, else the toplevel."""
    result = git(start, "rev-parse", "--show-superproject-working-tree", "--show-toplevel")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return Path(lines[0]).resolve()


def repos(root: Path) -> list[Repo]:
    """Umbrella first, then submodules in .gitmodules order (sorted by path)."""
    subs = sorted(submodule_paths(root))
    return [Repo(UMBRELLA_LABEL, root, True)] + [Repo(s, root / s, False) for s in subs]


def select(all_repos: list[Repo], only: list[str] | None) -> list[Repo]:
    """Restrict to the umbrella plus the named submodules (umbrella is always kept)."""
    if not only:
        return all_repos
    known = {r.label for r in all_repos if not r.is_umbrella}
    unknown = [name.rstrip("/\\") for name in only if name.rstrip("/\\") not in known]
    if unknown:
        raise BranchError(
            f"unknown submodule(s): {', '.join(unknown)} (known: {', '.join(sorted(known))})"
        )
    wanted = {name.rstrip("/\\") for name in only}
    return [r for r in all_repos if r.is_umbrella or r.label in wanted]


# --- queries ---------------------------------------------------------------


def current_branch(repo: Path) -> str | None:
    name = git(repo, "branch", "--show-current").stdout.strip()
    return name or None


def has_local(repo: Path, name: str) -> bool:
    return (
        git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{name}", check=False).returncode
        == 0
    )


def has_remote(repo: Path, name: str) -> bool:
    ref = f"refs/remotes/{REMOTE}/{name}"
    return git(repo, "show-ref", "--verify", "--quiet", ref, check=False).returncode == 0


def default_branch(repo: Path) -> str | None:
    result = git(repo, "symbolic-ref", "--short", f"refs/remotes/{REMOTE}/HEAD", check=False)
    value = result.stdout.strip()
    return value.split("/", 1)[1] if result.returncode == 0 and "/" in value else None


def protected(repo: Path) -> set[str]:
    names = set(ALWAYS_PROTECTED)
    default = default_branch(repo)
    if default:
        names.add(default)
    return names


def dirty_count(repo: Path) -> int:
    out = git(repo, "status", "--porcelain", "--ignore-submodules=all").stdout
    return sum(1 for line in out.splitlines() if line.strip())


def upstream_counts(repo: Path) -> tuple[str, int, int] | None:
    """(upstream, behind, ahead) of HEAD, or None without an upstream."""
    up = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
    if up.returncode != 0:
        return None
    counts = git(repo, "rev-list", "--left-right", "--count", "@{u}...HEAD", check=False)
    if counts.returncode != 0:
        return None
    behind, ahead = (int(x) for x in counts.stdout.split())
    return up.stdout.strip(), behind, ahead


def pointer_state(root: Path, sub: str) -> str:
    """How the umbrella's recorded pointer compares to the submodule's HEAD."""
    staged = git(root, "ls-files", "--stage", "--", sub).stdout.split()
    recorded = staged[1] if len(staged) >= 2 else ""
    head = git(root / sub, "rev-parse", "HEAD").stdout.strip()
    if recorded == head:
        return "pointer ok"
    committed = git(root, "ls-tree", "HEAD", "--", sub).stdout.split()
    in_head = committed[2] if len(committed) >= 3 else ""
    if recorded != in_head:
        return "pointer staged"
    return "pointer differs (git add " + sub + ")"


# --- commands --------------------------------------------------------------


def _say(repo: Repo, message: str) -> None:
    print(f"{repo.label:<14} {message}")


def _run_all(targets: list[Repo], action, verb: str) -> int:
    """Run ``action(repo)`` on each target; keep going after a failure, report at the end."""
    failed: list[str] = []
    for repo in targets:
        try:
            message = action(repo)
            if message:
                _say(repo, message)
        except subprocess.CalledProcessError as exc:
            _say(repo, f"FAILED {verb}: {exc.stderr}")
            failed.append(repo.label)
    if failed:
        print(f"\n{verb} failed in: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def status(root: Path, only: list[str] | None = None) -> int:
    for repo in select(repos(root), only):
        branch = current_branch(repo.path)
        if branch is None:
            sha = git(repo.path, "rev-parse", "--short", "HEAD").stdout.strip()
            parts = [f"(detached {sha})"]
        else:
            parts = [branch]
        up = upstream_counts(repo.path) if branch else None
        if up is None:
            parts.append("no upstream" if branch else "")
        else:
            name, behind, ahead = up
            sync = "in sync" if not (behind or ahead) else f"ahead {ahead}, behind {behind}"
            parts.append(f"{name}: {sync}")
        dirty = dirty_count(repo.path)
        parts.append(f"{dirty} changed" if dirty else "clean")
        if not repo.is_umbrella:
            parts.append(pointer_state(root, repo.label))
        _say(repo, " | ".join(p for p in parts if p))
    return 0


def list_branches(root: Path, only: list[str] | None = None) -> int:
    """Local branches across repositories, one line per branch name."""
    targets = select(repos(root), only)
    table: dict[str, list[str]] = {}
    for repo in targets:
        out = git(repo.path, "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout
        current = current_branch(repo.path)
        for name in out.split():
            mark = "*" if name == current else ""
            table.setdefault(name, []).append(mark + repo.label)
    for name in sorted(table):
        print(f"{name:<30} {', '.join(table[name])}")
    return 0


def new(root: Path, name: str, only: list[str] | None = None, base: str | None = None) -> int:
    """Create ``name`` and switch to it in every target repository."""
    targets = select(repos(root), only)
    if git(root, "check-ref-format", "--branch", name, check=False).returncode != 0:
        raise BranchError(f"invalid branch name: '{name}'")
    clashes = [r.label for r in targets if has_local(r.path, name)]
    if clashes:
        raise BranchError(
            f"branch '{name}' already exists in: {', '.join(clashes)} (use branch-switch instead)"
        )
    if base:
        missing = [
            r.label
            for r in targets
            if git(
                r.path, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}", check=False
            ).returncode
        ]
        if missing:
            raise BranchError(f"base '{base}' not found in: {', '.join(missing)}")

    def act(repo: Repo) -> str:
        args = ["switch", "-c", name] + ([base] if base else [])
        git(repo.path, *args)
        return f"created and switched to {name}" + (f" from {base}" if base else "")

    return _run_all(targets, act, "create")


def switch(
    root: Path,
    name: str,
    only: list[str] | None = None,
    create: bool = False,
    fetch: bool = True,
) -> int:
    """Switch every target to ``name`` (local, or tracking origin/<name>).

    A repository with neither a local nor a remote ``name`` is an error unless
    ``create``, which branches it from its current HEAD.
    """
    targets = select(repos(root), only)
    if fetch:
        for repo in targets:
            git(repo.path, "fetch", "--quiet", REMOTE, check=False)
    missing = [
        r.label for r in targets if not has_local(r.path, name) and not has_remote(r.path, name)
    ]
    if missing and not create:
        raise BranchError(
            f"branch '{name}' exists neither locally nor on {REMOTE} in: {', '.join(missing)}"
            " (pass --create to branch those from their current HEAD, or --only to skip them)"
        )

    def act(repo: Repo) -> str:
        if current_branch(repo.path) == name:
            return f"already on {name}"
        if has_local(repo.path, name):
            git(repo.path, "switch", name)
            return f"switched to {name}"
        if has_remote(repo.path, name):
            git(repo.path, "switch", "--track", f"{REMOTE}/{name}")
            return f"switched to {name} (tracking {REMOTE}/{name})"
        git(repo.path, "switch", "-c", name)
        return f"created and switched to {name}"

    return _run_all(targets, act, "switch")


def delete(
    root: Path,
    name: str,
    only: list[str] | None = None,
    force: bool = False,
    remote: bool = False,
) -> int:
    """Delete ``name`` locally (and on origin with ``remote``) wherever it exists."""
    targets = select(repos(root), only)
    guarded = [r.label for r in targets if name in protected(r.path)]
    if guarded:
        raise BranchError(
            f"refusing to delete protected branch '{name}' (in: {', '.join(guarded)})"
        )
    on_it = [r.label for r in targets if current_branch(r.path) == name]
    if on_it:
        raise BranchError(
            f"currently on '{name}' in: {', '.join(on_it)} (switch away first, e.g. just branch-switch main)"
        )
    if remote:
        for repo in targets:
            git(repo.path, "fetch", "--quiet", "--prune", REMOTE, check=False)
    if not force:
        unmerged = [
            r.label for r in targets if has_local(r.path, name) and not _merged(r.path, name)
        ]
        if unmerged:
            raise BranchError(
                f"'{name}' is not merged into its upstream or HEAD in: {', '.join(unmerged)}"
                " (merge or push it first, or pass --force)"
            )

    def act(repo: Repo) -> str:
        done: list[str] = []
        if has_local(repo.path, name):
            git(repo.path, "branch", "-D" if force else "-d", name)
            done.append("local")
        if remote and has_remote(repo.path, name):
            git(repo.path, "push", "--quiet", REMOTE, "--delete", name)
            done.append(REMOTE)
        return f"deleted {name} ({', '.join(done)})" if done else f"no {name} here"

    return _run_all(targets, act, "delete")


def _merged(repo: Path, name: str) -> bool:
    """True if ``git branch -d`` would succeed: merged into its upstream, or into HEAD."""
    up = git(repo, "rev-parse", "--abbrev-ref", f"{name}@{{u}}", check=False)
    target = up.stdout.strip() if up.returncode == 0 else "HEAD"
    return git(repo, "merge-base", "--is-ancestor", name, target, check=False).returncode == 0


def push(root: Path, only: list[str] | None = None) -> int:
    """Push the current branch of each target, submodules first, setting upstream."""
    targets = select(repos(root), only)
    detached = [r.label for r in targets if current_branch(r.path) is None]
    if detached:
        raise BranchError(f"detached HEAD in: {', '.join(detached)} (switch to a branch first)")
    ordered = [r for r in targets if not r.is_umbrella] + [r for r in targets if r.is_umbrella]

    def act(repo: Repo) -> str:
        branch = current_branch(repo.path)
        up = upstream_counts(repo.path)
        if up is not None and up[2] == 0:
            return f"{branch}: nothing to push"
        git(repo.path, "push", "--quiet", "--set-upstream", REMOTE, f"HEAD:refs/heads/{branch}")
        return f"pushed {branch}"

    # Stop before the umbrella if any submodule push failed, so it never points at an unpushed commit.
    subs = [r for r in ordered if not r.is_umbrella]
    code = _run_all(subs, act, "push")
    if code:
        print("umbrella not pushed: fix the submodule push first", file=sys.stderr)
        return code
    return _run_all([r for r in ordered if r.is_umbrella], act, "push")


def pull(root: Path, only: list[str] | None = None) -> int:
    """Fast-forward each target's current branch from its upstream (umbrella first).

    Unlike ``sub-sync`` this keeps every repository on its current branch.
    """
    targets = select(repos(root), only)

    def act(repo: Repo) -> str:
        branch = current_branch(repo.path)
        if branch is None:
            return "detached HEAD: skipped"
        git(repo.path, "fetch", "--quiet", "--prune", REMOTE)
        up = upstream_counts(repo.path)
        if up is None:
            return f"{branch}: no upstream, skipped"
        if up[1] == 0:
            return f"{branch}: up to date"
        git(repo.path, "merge", "--ff-only", "--quiet", "@{u}")
        return f"{branch}: fast-forwarded {up[1]} commit(s)"

    return _run_all(targets, act, "pull")
