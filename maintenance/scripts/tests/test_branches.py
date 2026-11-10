from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from branches import core  # noqa: E402


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def configure(repo: Path) -> None:
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "core.hooksPath", "/dev/null")
    git(repo, "config", "protocol.file.allow", "always")


def commit(repo: Path, name: str, text: str) -> None:
    (repo / name).write_text(text, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", f"add {name}")


def bare_with_main(tmp_path: Path, name: str) -> Path:
    work = tmp_path / f"{name}-seed"
    work.mkdir()
    git(work, "init", "-q", "-b", "main")
    configure(work)
    commit(work, "a.txt", "v1\n")
    bare = tmp_path / f"{name}.git"
    git(tmp_path, "clone", "-q", "--bare", str(work), str(bare))
    return bare


def clone_umbrella(tmp_path: Path, umbrella_bare: Path, dest: str) -> Path:
    root = tmp_path / dest
    git(tmp_path, "clone", "-q", "--recurse-submodules", str(umbrella_bare), str(root))
    configure(root)
    configure(root / "sub")
    git(root / "sub", "switch", "-q", "main")
    return root


@pytest.fixture
def setup(tmp_path: Path) -> tuple[Path, Path]:
    sub_bare = bare_with_main(tmp_path, "sub")
    seed = tmp_path / "umbrella-seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    configure(seed)
    git(seed, "submodule", "add", "-q", str(sub_bare), "sub")
    git(seed, "commit", "-q", "-m", "add sub")
    umbrella_bare = tmp_path / "umbrella.git"
    git(tmp_path, "clone", "-q", "--bare", str(seed), str(umbrella_bare))
    return clone_umbrella(tmp_path, umbrella_bare, "pc1"), clone_umbrella(
        tmp_path, umbrella_bare, "pc2"
    )


def branch(repo: Path) -> str:
    return git(repo, "branch", "--show-current")


def test_new_push_switch_pull_delete_across_machines(setup: tuple[Path, Path]) -> None:
    pc1, pc2 = setup

    assert core.new(pc1, "feat") == 0
    assert branch(pc1) == branch(pc1 / "sub") == "feat"

    commit(pc1 / "sub", "b.txt", "x\n")
    git(pc1, "add", "sub")
    git(pc1, "commit", "-q", "-m", "bump sub")
    assert core.push(pc1) == 0

    # Second machine picks the branch up from origin in every repository.
    assert core.switch(pc2, "feat") == 0
    assert branch(pc2) == branch(pc2 / "sub") == "feat"
    assert (pc2 / "sub" / "b.txt").exists()

    commit(pc1 / "sub", "c.txt", "y\n")
    assert core.push(pc1) == 0
    assert core.pull(pc2) == 0
    assert branch(pc2 / "sub") == "feat"
    assert (pc2 / "sub" / "c.txt").exists()

    # Deleting refuses while on the branch, then deletes local and remote.
    with pytest.raises(core.BranchError):
        core.delete(pc1, "feat", remote=True)
    assert core.switch(pc1, "main", fetch=False) == 0
    assert core.delete(pc1, "feat", remote=True) == 0
    assert git(pc1 / "sub", "branch", "--list", "feat") == ""
    assert git(pc1 / "sub", "ls-remote", "--heads", "origin", "feat") == ""


def test_prechecks_change_nothing(setup: tuple[Path, Path]) -> None:
    pc1, _ = setup
    git(pc1 / "sub", "branch", "taken")
    with pytest.raises(core.BranchError):
        core.new(pc1, "taken")
    assert branch(pc1) == "main"  # umbrella was not switched before the clash was found

    with pytest.raises(core.BranchError):
        core.switch(pc1, "nowhere", fetch=False)
    assert core.switch(pc1, "nowhere", create=True, fetch=False) == 0
    assert branch(pc1) == branch(pc1 / "sub") == "nowhere"

    with pytest.raises(core.BranchError):
        core.delete(pc1, "main")


def test_delete_refuses_unmerged_without_force(setup: tuple[Path, Path]) -> None:
    pc1, _ = setup
    core.new(pc1, "wip")
    commit(pc1 / "sub", "w.txt", "w\n")
    core.switch(pc1, "main", fetch=False)
    with pytest.raises(core.BranchError):
        core.delete(pc1, "wip")
    assert core.delete(pc1, "wip", force=True) == 0


def test_only_limits_submodules(setup: tuple[Path, Path]) -> None:
    pc1, _ = setup
    with pytest.raises(core.BranchError):
        core.select(core.repos(pc1), ["missing"])
    assert [r.label for r in core.select(core.repos(pc1), ["sub"])] == [core.UMBRELLA_LABEL, "sub"]
