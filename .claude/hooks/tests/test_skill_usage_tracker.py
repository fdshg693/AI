#!/usr/bin/env python3
"""`skill_usage_tracker.py`（PostToolUse hook）と `_skill_frontmatter.py` のテスト。

使い方（リポジトリルートから）:

    uv run pytest .claude/hooks/tests/test_skill_usage_tracker.py

パース・解決系の関数は直接importして単体テストし、実際のフック起動時の挙動
（stdin JSON解釈・session_id/auto-enquete判定・state書き込み）はサブプロセスとして
起動し、独立した一時プロジェクトディレクトリ（CLAUDE_PROJECT_DIR）とホーム
ディレクトリ（HOME/USERPROFILE、~/.claude/skills スキャンをテストに影響させない
ため）に対してエンドツーエンドで検証する。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _lib import skill_frontmatter as fm  # noqa: E402
import skill_usage_tracker as hook  # noqa: E402
from _lib import skill_enquete_state as state_mod  # noqa: E402

SCRIPT_PATH = HOOKS_DIR / "skill_usage_tracker.py"


def _write_skill(dir_path, name=None, auto_enquete=None, description="does X"):
    dir_path.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    if name is not None:
        lines.append(f"name: {name}")
    lines.append(f"description: {description}")
    if auto_enquete is not None:
        lines.append(f"auto-enquete: {'true' if auto_enquete else 'false'}")
    lines.append("---")
    lines.append("")
    lines.append("Body text.")
    (dir_path / "SKILL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# _skill_frontmatter.read_frontmatter
# ---------------------------------------------------------------------------


def test_read_frontmatter_valid(tmp_path):
    _write_skill(tmp_path, name="foo", auto_enquete=True)
    data = fm.read_frontmatter(tmp_path / "SKILL.md")
    assert data["name"] == "foo"
    assert data["auto-enquete"] is True


def test_read_frontmatter_no_frontmatter_returns_none(tmp_path):
    (tmp_path / "SKILL.md").write_text("just body, no frontmatter\n", encoding="utf-8")
    assert fm.read_frontmatter(tmp_path / "SKILL.md") is None


def test_read_frontmatter_invalid_yaml_returns_none(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: [unterminated\n---\nbody\n", encoding="utf-8")
    assert fm.read_frontmatter(tmp_path / "SKILL.md") is None


def test_read_frontmatter_missing_file_returns_none(tmp_path):
    assert fm.read_frontmatter(tmp_path / "does-not-exist.md") is None


# ---------------------------------------------------------------------------
# _skill_frontmatter.find_skill_dir_by_name
# ---------------------------------------------------------------------------


def test_find_skill_dir_by_frontmatter_name(tmp_path):
    skill_dir = tmp_path / "on-disk-dirname"
    _write_skill(skill_dir, name="real-name", auto_enquete=True)
    found = fm.find_skill_dir_by_name("real-name", [tmp_path])
    assert found == skill_dir


def test_find_skill_dir_falls_back_to_dirname(tmp_path):
    skill_dir = tmp_path / "my-skill"
    _write_skill(skill_dir, name=None)
    found = fm.find_skill_dir_by_name("my-skill", [tmp_path])
    assert found == skill_dir


def test_find_skill_dir_name_match_wins_over_dirname_fallback(tmp_path):
    decoy_dir = tmp_path / "target-name"
    _write_skill(decoy_dir, name="not-target-name")
    real_dir = tmp_path / "other-dirname"
    _write_skill(real_dir, name="target-name")
    found = fm.find_skill_dir_by_name("target-name", [tmp_path])
    assert found == real_dir


def test_find_skill_dir_no_match_returns_none(tmp_path):
    _write_skill(tmp_path / "unrelated", name="unrelated")
    assert fm.find_skill_dir_by_name("nope", [tmp_path]) is None


def test_find_skill_dir_missing_root_is_skipped(tmp_path):
    assert fm.find_skill_dir_by_name("anything", [tmp_path / "does-not-exist"]) is None


# ---------------------------------------------------------------------------
# skill_usage_tracker.resolve_skill_md_for_read
# ---------------------------------------------------------------------------


def test_resolve_skill_md_for_read_matches_skill_md(tmp_path):
    _write_skill(tmp_path, name="foo")
    resolved = hook.resolve_skill_md_for_read(str(tmp_path / "SKILL.md"))
    assert resolved == (tmp_path / "SKILL.md").resolve()


def test_resolve_skill_md_for_read_rejects_other_filenames(tmp_path):
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    assert hook.resolve_skill_md_for_read(str(tmp_path / "README.md")) is None


def test_resolve_skill_md_for_read_missing_file_returns_none(tmp_path):
    assert hook.resolve_skill_md_for_read(str(tmp_path / "SKILL.md")) is None


# ---------------------------------------------------------------------------
# skill_usage_tracker.load_roots
# ---------------------------------------------------------------------------


def test_load_roots_reads_config_and_appends_home_skills(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    config_dir = tmp_path / ".claude" / "hooks" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "skill_usage_tracker.yaml").write_text(
        "roots:\n  - .claude/skills\n", encoding="utf-8"
    )
    roots = hook.load_roots(tmp_path)
    assert (tmp_path / ".claude" / "skills") in roots
    assert roots[-1] == Path.home() / ".claude" / "skills"


def test_load_roots_no_config_defaults_to_dotclaude_skills_and_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    roots = hook.load_roots(tmp_path)
    assert roots == [tmp_path / ".claude" / "skills", Path.home() / ".claude" / "skills"]


# ---------------------------------------------------------------------------
# End-to-end (subprocess) — actual hook invocation via stdin JSON
# ---------------------------------------------------------------------------


def _run_hook(project_dir, home_dir, payload):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env["HOME"] = str(home_dir)
    env["USERPROFILE"] = str(home_dir)
    env.pop("HOOK_LOG", None)
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=30,
    )
    return result


def _state_file(project_dir, session_id):
    return state_mod.state_path(project_dir, session_id)


def test_e2e_read_skill_md_with_auto_enquete_records(tmp_path):
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    skill_dir = project_dir / ".claude" / "skills" / "target-skill"
    _write_skill(skill_dir, name="target-skill", auto_enquete=True)

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": str(skill_dir / "SKILL.md")},
        "session_id": "sess-1",
    }
    result = _run_hook(project_dir, home_dir, payload)
    assert result.returncode == 0, result.stderr

    state = state_mod.load_state(_state_file(project_dir, "sess-1"))
    assert "target-skill" in state["skills"]
    assert state["skills"]["target-skill"]["dir"] == skill_dir.resolve().as_posix()


def test_e2e_read_skill_md_without_auto_enquete_is_noop(tmp_path):
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    skill_dir = project_dir / ".claude" / "skills" / "plain-skill"
    _write_skill(skill_dir, name="plain-skill", auto_enquete=False)

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": str(skill_dir / "SKILL.md")},
        "session_id": "sess-2",
    }
    result = _run_hook(project_dir, home_dir, payload)
    assert result.returncode == 0, result.stderr
    assert not _state_file(project_dir, "sess-2").exists()


def test_e2e_read_non_skill_md_is_noop(tmp_path):
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    other_file = project_dir / "README.md"
    other_file.parent.mkdir(parents=True, exist_ok=True)
    other_file.write_text("hello", encoding="utf-8")

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": str(other_file)},
        "session_id": "sess-3",
    }
    result = _run_hook(project_dir, home_dir, payload)
    assert result.returncode == 0, result.stderr
    assert not _state_file(project_dir, "sess-3").exists()


def test_e2e_skill_tool_invocation_resolves_name_and_records(tmp_path):
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    skill_dir = project_dir / ".claude" / "skills" / "on-disk-name"
    _write_skill(skill_dir, name="my-skill", auto_enquete=True)

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Skill",
        "tool_input": {"skill": "my-skill"},
        "session_id": "sess-4",
    }
    result = _run_hook(project_dir, home_dir, payload)
    assert result.returncode == 0, result.stderr

    state = state_mod.load_state(_state_file(project_dir, "sess-4"))
    assert "my-skill" in state["skills"]


def test_e2e_skill_tool_invocation_with_plugin_prefix(tmp_path):
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    skill_dir = project_dir / ".claude" / "skills" / "prefixed-skill"
    _write_skill(skill_dir, name="prefixed-skill", auto_enquete=True)

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Skill",
        "tool_input": {"skill": "myplugin:prefixed-skill"},
        "session_id": "sess-5",
    }
    result = _run_hook(project_dir, home_dir, payload)
    assert result.returncode == 0, result.stderr

    state = state_mod.load_state(_state_file(project_dir, "sess-5"))
    assert "prefixed-skill" in state["skills"]


def test_e2e_missing_session_id_is_noop(tmp_path):
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    skill_dir = project_dir / ".claude" / "skills" / "target-skill"
    _write_skill(skill_dir, name="target-skill", auto_enquete=True)

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": str(skill_dir / "SKILL.md")},
    }
    result = _run_hook(project_dir, home_dir, payload)
    assert result.returncode == 0, result.stderr


def test_e2e_other_tool_is_noop(tmp_path):
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
        "session_id": "sess-6",
    }
    result = _run_hook(project_dir, home_dir, payload)
    assert result.returncode == 0, result.stderr
    assert not _state_file(project_dir, "sess-6").exists()
