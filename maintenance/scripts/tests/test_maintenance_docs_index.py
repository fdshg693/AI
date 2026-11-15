from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from okf_docs import generate_maintenance_docs_index as gen  # noqa: E402

INTRO = "# maintenance/docs/\n\n手書きの導入文。\n\n"
OUTRO = "\n末尾の手書き。\n"


def write_doc(docs: Path, stem: str, description: str | None) -> None:
    front = "type: Concept\ntitle: t\n"
    if description is not None:
        front += f"description: {description}\n"
    (docs / f"{stem}.md").write_text(f"---\n{front}---\n\n# {stem}\n", encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    docs = tmp_path / "maintenance" / "docs"
    docs.mkdir(parents=True)
    write_doc(docs, "zeta", "Last one.")
    write_doc(docs, "alpha", "First one.")
    (docs / "index.md").write_text(
        f"{INTRO}{gen.BEGIN_MARKER}\n- stale\n{gen.END_MARKER}{OUTRO}", encoding="utf-8"
    )
    return tmp_path


def index_text(repo: Path) -> str:
    return (repo / "maintenance" / "docs" / "index.md").read_text(encoding="utf-8")


def test_generates_sorted_list_without_index(repo: Path) -> None:
    assert gen.main([], repo_root=repo) == 0
    text = index_text(repo)
    assert "- [alpha](alpha.md) — First one.\n- [zeta](zeta.md) — Last one.\n" in text
    assert "[index]" not in text
    assert "- stale" not in text


def test_keeps_text_outside_markers(repo: Path) -> None:
    gen.main([], repo_root=repo)
    text = index_text(repo)
    assert text.startswith(INTRO + gen.BEGIN_MARKER)
    assert text.endswith(gen.END_MARKER + OUTRO)


def test_folded_multiline_description_becomes_one_line(repo: Path) -> None:
    docs = repo / "maintenance" / "docs"
    (docs / "beta.md").write_text(
        "---\ndescription: >-\n  Spans\n  two lines.\n---\n", encoding="utf-8"
    )
    gen.main([], repo_root=repo)
    assert "- [beta](beta.md) — Spans two lines.\n" in index_text(repo)


@pytest.mark.parametrize("content", ["# no frontmatter\n", "---\ntitle: t\n---\n"])
def test_missing_frontmatter_or_description_fails(
    repo: Path, content: str, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "maintenance" / "docs" / "broken.md").write_text(content, encoding="utf-8")
    before = index_text(repo)
    assert gen.main([], repo_root=repo) == 1
    assert "broken.md" in capsys.readouterr().err
    assert index_text(repo) == before


def test_does_not_write_when_unchanged(repo: Path) -> None:
    gen.main([], repo_root=repo)
    index = repo / "maintenance" / "docs" / "index.md"
    mtime = index.stat().st_mtime_ns
    assert gen.main([], repo_root=repo) == 0
    assert index.stat().st_mtime_ns == mtime


def test_check_reports_stale_without_writing(repo: Path) -> None:
    before = index_text(repo)
    assert gen.main(["--check"], repo_root=repo) == 1
    assert index_text(repo) == before
    gen.main([], repo_root=repo)
    assert gen.main(["--check"], repo_root=repo) == 0


def test_missing_markers_fails(repo: Path) -> None:
    (repo / "maintenance" / "docs" / "index.md").write_text(INTRO, encoding="utf-8")
    assert gen.main([], repo_root=repo) == 1
