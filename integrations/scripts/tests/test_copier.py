from __future__ import annotations

from pathlib import Path

from skill_deploy.copier import copy_item


def test_copy_item_directory_copies_contents(tmp_path: Path) -> None:
    source = tmp_path / "src" / "skill-a"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("hello", encoding="utf-8")

    dest_dir = tmp_path / "dest"
    copy_item(source, dest_dir, dry_run=False)

    copied = dest_dir / "skill-a" / "SKILL.md"
    assert copied.read_text(encoding="utf-8") == "hello"


def test_copy_item_directory_ignores_pycache(tmp_path: Path) -> None:
    source = tmp_path / "src" / "skill-a"
    (source / "__pycache__").mkdir(parents=True)
    (source / "__pycache__" / "mod.pyc").write_text("junk", encoding="utf-8")
    (source / "SKILL.md").write_text("hello", encoding="utf-8")

    dest_dir = tmp_path / "dest"
    copy_item(source, dest_dir, dry_run=False)

    assert not (dest_dir / "skill-a" / "__pycache__").exists()
    assert (dest_dir / "skill-a" / "SKILL.md").exists()


def test_copy_item_directory_excludes_dotenv_but_keeps_example(tmp_path: Path) -> None:
    source = tmp_path / "src" / "skill-a"
    source.mkdir(parents=True)
    (source / ".env").write_text("SECRET_KEY=do-not-leak", encoding="utf-8")
    (source / ".env.example").write_text("SECRET_KEY=", encoding="utf-8")

    dest_dir = tmp_path / "dest"
    copy_item(source, dest_dir, dry_run=False)

    assert not (dest_dir / "skill-a" / ".env").exists()
    assert (dest_dir / "skill-a" / ".env.example").exists()


def test_copy_item_directory_clean_replaces_stale_files(tmp_path: Path) -> None:
    source = tmp_path / "src" / "skill-a"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("new", encoding="utf-8")

    dest_dir = tmp_path / "dest"
    existing = dest_dir / "skill-a"
    existing.mkdir(parents=True)
    (existing / "stale.txt").write_text("should be removed", encoding="utf-8")

    copy_item(source, dest_dir, dry_run=False)

    assert not (dest_dir / "skill-a" / "stale.txt").exists()
    assert (dest_dir / "skill-a" / "SKILL.md").read_text(encoding="utf-8") == "new"


def test_copy_item_dry_run_touches_nothing(tmp_path: Path) -> None:
    source = tmp_path / "src" / "skill-a"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("hello", encoding="utf-8")

    dest_dir = tmp_path / "dest"
    description = copy_item(source, dest_dir, dry_run=True)

    assert not dest_dir.exists()
    assert "skill-a" in description


def test_copy_item_file_overwrites_existing(tmp_path: Path) -> None:
    source = tmp_path / "src" / "note.md"
    source.parent.mkdir(parents=True)
    source.write_text("new content", encoding="utf-8")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    (dest_dir / "note.md").write_text("old content", encoding="utf-8")

    copy_item(source, dest_dir, dry_run=False)

    assert (dest_dir / "note.md").read_text(encoding="utf-8") == "new content"
