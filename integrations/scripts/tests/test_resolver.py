from __future__ import annotations

from pathlib import Path

import pytest

from skill_deploy.models import ResolveError, Target
from skill_deploy.resolver import expand_item, resolve_dest, resolve_target


def make_skill(repo_root: Path, relative: str) -> Path:
    path = repo_root / relative
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text("dummy", encoding="utf-8")
    return path


def test_expand_item_plain_path(repo_root: Path) -> None:
    make_skill(repo_root, "plugins/skills/foo")
    paths, warnings = expand_item("plugins/skills/foo", {}, repo_root)
    assert paths == [repo_root / "plugins/skills/foo"]
    assert warnings == []


def test_expand_item_plain_path_missing_raises(repo_root: Path) -> None:
    with pytest.raises(ResolveError):
        expand_item("plugins/skills/missing", {}, repo_root)


def test_expand_item_glob_expands_sorted(repo_root: Path) -> None:
    make_skill(repo_root, "plugins/skills/bbb")
    make_skill(repo_root, "plugins/skills/aaa")
    paths, warnings = expand_item("plugins/skills/*", {}, repo_root)
    assert paths == [repo_root / "plugins/skills/aaa", repo_root / "plugins/skills/bbb"]
    assert warnings == []


def test_expand_item_glob_no_match_warns(repo_root: Path) -> None:
    (repo_root / "plugins").mkdir()
    paths, warnings = expand_item("plugins/skills/*", {}, repo_root)
    assert paths == []
    assert len(warnings) == 1
    assert "plugins/skills/*" in warnings[0]


def test_expand_item_set_reference_expands_all_entries(repo_root: Path) -> None:
    make_skill(repo_root, "a")
    make_skill(repo_root, "b")
    sets = {"my-set": ["a", "b"]}
    paths, warnings = expand_item("@my-set", sets, repo_root)
    assert paths == [repo_root / "a", repo_root / "b"]
    assert warnings == []


def test_expand_item_set_can_reference_another_set(repo_root: Path) -> None:
    make_skill(repo_root, "a")
    sets = {"inner": ["a"], "outer": ["@inner"]}
    paths, warnings = expand_item("@outer", sets, repo_root)
    assert paths == [repo_root / "a"]


def test_expand_item_unknown_set_raises(repo_root: Path) -> None:
    with pytest.raises(ResolveError):
        expand_item("@does-not-exist", {}, repo_root)


def test_expand_item_circular_set_raises(repo_root: Path) -> None:
    sets = {"a": ["@b"], "b": ["@a"]}
    with pytest.raises(ResolveError):
        expand_item("@a", sets, repo_root)


def test_resolve_dest_absolute_passthrough(repo_root: Path, tmp_path: Path) -> None:
    absolute = tmp_path / "somewhere" / "else"
    result = resolve_dest(str(absolute), repo_root)
    assert result == absolute.resolve()


def test_resolve_dest_relative_is_anchored_to_repo_root(repo_root: Path) -> None:
    result = resolve_dest("some/dest", repo_root)
    assert result == (repo_root / "some/dest").resolve()


def test_resolve_dest_expands_env_vars(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_TEST_DEST_VAR", "injected")
    result = resolve_dest("$MY_TEST_DEST_VAR/dest", repo_root)
    assert result == (repo_root / "injected/dest").resolve()


def test_resolve_target_builds_copies_and_dedupes(repo_root: Path) -> None:
    make_skill(repo_root, "plugins/skills/foo")
    make_skill(repo_root, "plugins/skills/bar")
    target = Target(
        name="t1",
        dest="dest-dir",
        items=["plugins/skills/foo", "plugins/skills/*"],
        source_file=Path("dummy.yaml"),
    )
    copies, warnings = resolve_target(target, {}, repo_root)

    assert warnings == []
    sources = [c.source for c in copies]
    # foo appears once even though it matches both the explicit item and the glob.
    assert sources == [repo_root / "plugins/skills/foo", repo_root / "plugins/skills/bar"]
    assert all(c.dest_dir == (repo_root / "dest-dir").resolve() for c in copies)
    assert all(c.target_name == "t1" for c in copies)


def test_resolve_target_wraps_resolve_error_with_context(repo_root: Path) -> None:
    target = Target(
        name="t1",
        dest="dest-dir",
        items=["@missing-set"],
        source_file=Path("dummy.yaml"),
    )
    with pytest.raises(ResolveError, match="t1"):
        resolve_target(target, {}, repo_root)
