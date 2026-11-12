from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import repo_git  # noqa: E402


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "test")
    git(path, "config", "commit.gpgsign", "false")
    git(path, "config", "core.hooksPath", "/dev/null")


def test_staged_files_show_and_add_reach_into_submodules(tmp_path: Path) -> None:
    upstream = tmp_path / "upstream"
    init_repo(upstream)
    (upstream / "a.txt").write_text("v1\n", encoding="utf-8")
    git(upstream, "add", "a.txt")
    git(upstream, "commit", "-q", "-m", "init")

    root = tmp_path / "umbrella"
    init_repo(root)
    (root / "top.txt").write_text("top\n", encoding="utf-8")
    git(root, "add", "top.txt")
    git(root, "submodule", "add", "-q", str(upstream), "sub")
    git(root, "commit", "-q", "-m", "init")

    sub = root / "sub"
    git(sub, "config", "user.email", "test@example.com")
    git(sub, "config", "user.name", "test")
    (sub / "a.txt").write_text("v2\n", encoding="utf-8")
    (sub / "b.txt").write_text("new\n", encoding="utf-8")
    git(sub, "add", "a.txt")
    (root / "top.txt").write_text("top2\n", encoding="utf-8")
    git(root, "add", "top.txt")

    assert repo_git.submodule_paths(root) == ["sub"]
    assert repo_git.owner(root, "sub/a.txt") == (sub, "a.txt")
    assert repo_git.owner(root, "subx/a.txt") == (root, "subx/a.txt")
    assert sorted(repo_git.staged_files(root)) == ["sub/a.txt", "top.txt"]
    assert repo_git.show(root, "HEAD", "sub/a.txt") == "v1\n"
    assert repo_git.show(root, "HEAD", "top.txt") == "top\n"
    assert repo_git.show(root, "HEAD", "sub/missing.txt") is None

    assert repo_git.add(root, "sub/b.txt").returncode == 0
    assert sorted(repo_git.staged_files(root)) == ["sub/a.txt", "sub/b.txt", "top.txt"]


def test_uninitialized_submodule_is_skipped(tmp_path: Path) -> None:
    root = tmp_path / "umbrella"
    init_repo(root)
    (root / ".gitmodules").write_text(
        '[submodule "sub"]\n\tpath = sub\n\turl = https://example.invalid/sub.git\n',
        encoding="utf-8",
    )
    (root / "sub").mkdir()
    assert repo_git.submodule_paths(root) == []
    assert repo_git.staged_files(root) == []


def test_staged_files_ignore_hook_env_of_a_submodule_commit(tmp_path: Path, monkeypatch) -> None:
    """A hook of a commit inside a submodule inherits GIT_DIR/GIT_INDEX_FILE for
    that submodule; the umbrella's own git calls must not read its index."""
    upstream = tmp_path / "upstream"
    init_repo(upstream)
    (upstream / "a.txt").write_text("v1\n", encoding="utf-8")
    git(upstream, "add", "a.txt")
    git(upstream, "commit", "-q", "-m", "init")

    root = tmp_path / "umbrella"
    init_repo(root)
    git(root, "submodule", "add", "-q", str(upstream), "sub")
    git(root, "commit", "-q", "-m", "init")

    sub = root / "sub"
    (sub / "a.txt").write_text("v2\n", encoding="utf-8")
    git(sub, "add", "a.txt")

    sub_git_dir = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=sub,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.setenv("GIT_DIR", sub_git_dir)
    monkeypatch.setenv("GIT_INDEX_FILE", str(Path(sub_git_dir) / "index"))
    monkeypatch.setenv("GIT_PREFIX", "")

    assert repo_git.staged_files(root) == ["sub/a.txt"]
    assert repo_git.show(root, "HEAD", "sub/a.txt") == "v1\n"
