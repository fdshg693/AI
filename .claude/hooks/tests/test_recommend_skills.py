#!/usr/bin/env python3
"""`recommend_skills.py`（UserPromptSubmit hook）のテスト。

使い方（リポジトリルートから）:

    uv run pytest .claude/hooks/tests/test_recommend_skills.py

このフックは `import yaml` と（AI呼び出し経路では）`import aim_cli` に依存しており、
どちらもこのリポジトリのルート uv workspace（`pyproject.toml`）にのみインストール
されている。そのため本テストは素の `python`/`pytest` ではなく、必ず
`uv run pytest ...`（リポジトリルートから）で実行すること。

パース系・収集系の関数は直接importして単体テストし、実際のフック起動時の挙動
（stdin JSON解釈・config欠如時のno-op・event判定）はサブプロセスとして起動し、
独立した一時プロジェクトディレクトリ（`CLAUDE_PROJECT_DIR`）に対してエンドツーエンド
で検証する。aimへの実際のAI呼び出しが発生する経路（skills収集成功後）はネットワーク・
APIキーに依存するため、ここではE2Eの対象にしない（no-opに落ちる経路のみを検証する）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import recommend_skills as hook  # noqa: E402

SCRIPT_PATH = HOOKS_DIR / "recommend_skills.py"


def _write_skill(dir_path, name=None, description="does something useful", extra=""):
    dir_path.mkdir(parents=True, exist_ok=True)
    frontmatter = "---\n"
    if name is not None:
        frontmatter += f"name: {name}\n"
    frontmatter += f"description: {description}\n"
    frontmatter += extra
    frontmatter += "---\n\nBody text.\n"
    (dir_path / "SKILL.md").write_text(frontmatter, encoding="utf-8")


# ---------------------------------------------------------------------------
# read_skill
# ---------------------------------------------------------------------------


def test_read_skill_valid_frontmatter(tmp_path):
    skill_dir = tmp_path / "my-skill"
    _write_skill(skill_dir, name="my-skill", description="Use this for X.")
    entry = hook.read_skill(skill_dir / "SKILL.md")
    assert entry["name"] == "my-skill"
    assert entry["description"] == "Use this for X."
    assert entry["path"] == (skill_dir / "SKILL.md").as_posix()


def test_read_skill_missing_description_returns_none(tmp_path):
    skill_dir = tmp_path / "no-desc"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: no-desc\n---\nbody\n", encoding="utf-8")
    assert hook.read_skill(skill_dir / "SKILL.md") is None


def test_read_skill_name_falls_back_to_parent_dir(tmp_path):
    skill_dir = tmp_path / "folder-name"
    _write_skill(skill_dir, name=None, description="Some description.")
    entry = hook.read_skill(skill_dir / "SKILL.md")
    assert entry["name"] == "folder-name"


def test_read_skill_invalid_yaml_returns_none(tmp_path):
    skill_dir = tmp_path / "bad-yaml"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: [unterminated\n---\nbody\n", encoding="utf-8")
    assert hook.read_skill(skill_dir / "SKILL.md") is None


def test_read_skill_no_frontmatter_returns_none(tmp_path):
    skill_dir = tmp_path / "plain"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("just a plain markdown file\n", encoding="utf-8")
    assert hook.read_skill(skill_dir / "SKILL.md") is None


# ---------------------------------------------------------------------------
# collect_skills
# ---------------------------------------------------------------------------


def test_collect_skills_dedup_by_name_first_root_wins(tmp_path):
    root_a = tmp_path / "roots_a"
    root_b = tmp_path / "roots_b"
    _write_skill(root_a / "dup", name="dup", description="from A")
    _write_skill(root_b / "dup", name="dup", description="from B")

    warnings = []
    skills = hook.collect_skills(
        tmp_path, ["roots_a", "roots_b"], max_skills=100, warnings=warnings
    )
    assert len(skills) == 1
    assert skills[0]["description"] == "from A"
    assert warnings == []


def test_collect_skills_ignores_missing_root(tmp_path):
    warnings = []
    skills = hook.collect_skills(tmp_path, ["does-not-exist"], max_skills=100, warnings=warnings)
    assert skills == []
    assert warnings == []


def test_collect_skills_respects_max_skills_cap(tmp_path):
    root = tmp_path / "roots"
    for i in range(5):
        _write_skill(root / f"skill-{i}", name=f"skill-{i}", description="d")

    warnings = []
    skills = hook.collect_skills(tmp_path, ["roots"], max_skills=2, warnings=warnings)
    assert len(skills) == 2
    assert any("capped" in w for w in warnings)


def test_collect_skills_recurses_nested_plugin_layout(tmp_path):
    root = tmp_path / "claude-plugins"
    _write_skill(root / "pluginA" / "skills" / "foo", name="foo", description="foo desc")
    _write_skill(root / "pluginB" / "skills" / "bar", name="bar", description="bar desc")

    warnings = []
    skills = hook.collect_skills(tmp_path, ["claude-plugins"], max_skills=100, warnings=warnings)
    names = {s["name"] for s in skills}
    assert names == {"foo", "bar"}


# ---------------------------------------------------------------------------
# make_batches
# ---------------------------------------------------------------------------


def test_make_batches_splits_by_size_and_sorts_by_name():
    skills = [{"name": n, "description": "d"} for n in ["c", "a", "b", "d", "e"]]
    batches = hook.make_batches(skills, batch_size=2)
    assert [s["name"] for s in batches[0]] == ["a", "b"]
    assert [s["name"] for s in batches[1]] == ["c", "d"]
    assert [s["name"] for s in batches[2]] == ["e"]


def test_make_batches_empty_input():
    assert hook.make_batches([], batch_size=30) == []


# ---------------------------------------------------------------------------
# parse_recommendations
# ---------------------------------------------------------------------------


def _batch(*names):
    return [{"name": n, "description": f"{n} desc", "path": f"/skills/{n}/SKILL.md"} for n in names]


def test_parse_recommendations_exact_match():
    batch = _batch("alpha", "beta")
    text = "alpha :: helps with alpha tasks\n"
    results = hook.parse_recommendations(text, batch)
    assert len(results) == 1
    assert results[0]["name"] == "alpha"
    assert results[0]["reason"] == "helps with alpha tasks"


def test_parse_recommendations_case_insensitive_match():
    batch = _batch("Alpha-Skill")
    text = "alpha-skill :: matches\n"
    results = hook.parse_recommendations(text, batch)
    assert len(results) == 1
    assert results[0]["name"] == "Alpha-Skill"


def test_parse_recommendations_ignores_hallucinated_name():
    batch = _batch("alpha")
    text = "made-up-skill :: not real\n"
    assert hook.parse_recommendations(text, batch) == []


def test_parse_recommendations_ignores_lines_without_delimiter():
    batch = _batch("alpha")
    text = "just some prose without the delimiter\n"
    assert hook.parse_recommendations(text, batch) == []


def test_parse_recommendations_dedupes_repeated_name():
    batch = _batch("alpha")
    text = "alpha :: first\nalpha :: second\n"
    results = hook.parse_recommendations(text, batch)
    assert len(results) == 1
    assert results[0]["reason"] == "first"


def test_parse_recommendations_strips_bullet_prefix():
    batch = _batch("alpha")
    text = "- alpha :: bulleted\n"
    results = hook.parse_recommendations(text, batch)
    assert len(results) == 1


def test_parse_recommendations_no_reason_falls_back_to_placeholder():
    batch = _batch("alpha")
    text = "alpha ::   \n"
    results = hook.parse_recommendations(text, batch)
    assert results[0]["reason"] == "(no reason given)"


def test_parse_recommendations_empty_response():
    batch = _batch("alpha")
    assert hook.parse_recommendations("", batch) == []


# ---------------------------------------------------------------------------
# End-to-end: run the hook as a subprocess against a sandboxed project dir
# (no-op paths only -- paths that reach aim_cli require network/API key and
# are intentionally out of scope here)
# ---------------------------------------------------------------------------


def _make_project(tmp_path):
    project = tmp_path / "project"
    hooks_dir = project / ".claude" / "hooks"
    config_dir = hooks_dir / "config"
    config_dir.mkdir(parents=True)
    import shutil

    shutil.copy(SCRIPT_PATH, hooks_dir / "recommend_skills.py")
    shutil.copytree(HOOKS_DIR / "_lib", hooks_dir / "_lib")
    return project, config_dir


def _run_hook(project, payload):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env.pop("HOOK_LOG", None)
    result = subprocess.run(
        [sys.executable, str(project / ".claude" / "hooks" / "recommend_skills.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return result


def test_e2e_wrong_event_is_noop(tmp_path):
    project, _ = _make_project(tmp_path)
    result = _run_hook(project, {"hook_event_name": "Stop"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_e2e_empty_prompt_is_noop(tmp_path):
    project, _ = _make_project(tmp_path)
    result = _run_hook(project, {"hook_event_name": "UserPromptSubmit", "prompt": "   "})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_e2e_unparsable_stdin_is_noop(tmp_path):
    project, _ = _make_project(tmp_path)
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project)
    result = subprocess.run(
        [sys.executable, str(project / ".claude" / "hooks" / "recommend_skills.py")],
        input="not json",
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_e2e_missing_config_is_noop(tmp_path):
    project, _ = _make_project(tmp_path)
    result = _run_hook(project, {"hook_event_name": "UserPromptSubmit", "prompt": "do something"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_e2e_no_roots_configured_is_noop(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "recommend_skills.yaml").write_text("roots: []\n", encoding="utf-8")
    result = _run_hook(project, {"hook_event_name": "UserPromptSubmit", "prompt": "do something"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_e2e_roots_with_no_skill_md_is_noop(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (project / "empty-root").mkdir()
    (config_dir / "recommend_skills.yaml").write_text("roots:\n  - empty-root\n", encoding="utf-8")
    result = _run_hook(project, {"hook_event_name": "UserPromptSubmit", "prompt": "do something"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


if __name__ == "__main__":
    raise SystemExit(
        subprocess.run([sys.executable, "-m", "pytest", str(Path(__file__)), "-v"]).returncode
    )
