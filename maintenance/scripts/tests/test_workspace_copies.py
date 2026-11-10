from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugin_meta.generate import generate_workspace_copies as gen  # noqa: E402
from skill.util.skill_frontmatter import (  # noqa: E402
    WORKSPACE_COPY_MARKER,
    find_skill_md_files,
)


def make_skill(root: Path, name: str) -> None:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = tmp_path / "skills" / "plugins" / "k" / "skills"
    for name in ("cline-a", "cline-b", "kilo-a"):
        make_skill(source, name)
    (source / "cline-a" / "__pycache__").mkdir()
    (source / "cline-a" / ".env").write_text("SECRET=1\n", encoding="utf-8")
    monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
    return tmp_path


def entry(**extra: object) -> dict:
    return {"from": "skills/plugins/k/skills", "include": ["cline-*"], **extra}


def test_copies_matching_skills_and_skips_ignored_files(repo: Path) -> None:
    assert gen.write_copy(entry(output_dir=".cline/skills")) == 2
    out = repo / ".cline" / "skills"
    assert sorted(p.name for p in out.iterdir() if p.is_dir()) == ["cline-a", "cline-b"]
    assert (out / WORKSPACE_COPY_MARKER).is_file()
    assert not (out / "cline-a" / ".env").exists()
    assert not (out / "cline-a" / "__pycache__").exists()


def test_rerun_replaces_previous_copy(repo: Path) -> None:
    gen.write_copy(entry(output_dir=".cline/skills"))
    stale = repo / ".cline" / "skills" / "cline-old"
    stale.mkdir()
    gen.write_copy(entry(output_dir=".cline/skills"))
    assert not stale.exists()


def test_refuses_unmarked_existing_dir(repo: Path) -> None:
    hand_made = repo / ".cline" / "skills" / "mine"
    hand_made.mkdir(parents=True)
    with pytest.raises(SystemExit):
        gen.write_copy(entry(output_dir=".cline/skills"))
    assert hand_made.is_dir()


def test_writes_plugin_json(repo: Path) -> None:
    gen.write_copy(entry(output_dir="_agents/plugins/p/skills", plugin_json={"name": "p"}))
    manifest = repo / "_agents" / "plugins" / "p" / "plugin.json"
    assert json.loads(manifest.read_text(encoding="utf-8")) == {"name": "p"}


def test_scanner_skips_marked_copies(repo: Path) -> None:
    gen.write_copy(entry(output_dir=".cline/skills"))
    found = {p.parent.name for p in find_skill_md_files(repo)}
    assert found == {"cline-a", "cline-b", "kilo-a"}
    assert all(".cline" not in p.parts for p in find_skill_md_files(repo))
