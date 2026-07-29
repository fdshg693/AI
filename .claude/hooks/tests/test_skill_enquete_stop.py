#!/usr/bin/env python3
"""`skill_enquete_stop.py`（Stop hook）のテスト。

使い方（リポジトリルートから）:

    uv run pytest .claude/hooks/tests/test_skill_enquete_stop.py

メッセージ組み立て関数は直接importして単体テストし、実際のフック起動時の挙動
（stdin JSON解釈・state読み込み・pending判定・stop_attemptsによる打ち切り）は
サブプロセスとして起動し、独立した一時プロジェクトディレクトリ（CLAUDE_PROJECT_DIR）
に対してエンドツーエンドで検証する。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import skill_enquete_stop as hook  # noqa: E402
from _lib import skill_enquete_state as state_mod  # noqa: E402

SCRIPT_PATH = HOOKS_DIR / "skill_enquete_stop.py"


# ---------------------------------------------------------------------------
# build_template / build_message
# ---------------------------------------------------------------------------


def test_build_template_contains_all_questions_and_no_placeholder_gaps():
    template = hook.build_template("my-skill", "sess-1")
    assert "skill: my-skill" in template
    assert "session_id: sess-1" in template
    for q in hook.QUESTIONS:
        assert q in template
    assert template.count("(ここに回答)") == len(hook.QUESTIONS)


def test_build_message_lists_each_pending_skill_and_its_target():
    pending = [
        {"name": "skill-a", "target": "/abs/path/skill-a/enquete/sess-1.md"},
        {"name": "skill-b", "target": "/abs/path/skill-b/enquete/sess-1.md"},
    ]
    message = hook.build_message(pending, "sess-1")
    assert "skill-a" in message
    assert "/abs/path/skill-a/enquete/sess-1.md" in message
    assert "skill-b" in message
    assert "/abs/path/skill-b/enquete/sess-1.md" in message


# ---------------------------------------------------------------------------
# End-to-end (subprocess) — actual hook invocation via stdin JSON
# ---------------------------------------------------------------------------


def _run_hook(project_dir, payload):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("HOOK_LOG", None)
    env.pop("SKILL_ENQUETE_MAX_ATTEMPTS", None)
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


def _seed_state(project_dir, session_id, skills, stop_attempts=0):
    path = state_mod.state_path(project_dir, session_id)
    state_mod.save_state(path, {"skills": skills, "stop_attempts": stop_attempts})
    return path


def test_e2e_no_state_file_allows_stop(tmp_path):
    result = _run_hook(tmp_path, {"session_id": "sess-1"})
    assert result.returncode == 0, result.stderr


def test_e2e_missing_session_id_allows_stop(tmp_path):
    result = _run_hook(tmp_path, {})
    assert result.returncode == 0, result.stderr


def test_e2e_pending_skill_blocks_with_instructions(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "target-skill"
    skill_dir.mkdir(parents=True)
    _seed_state(tmp_path, "sess-2", {"target-skill": {"dir": str(skill_dir)}})

    result = _run_hook(tmp_path, {"session_id": "sess-2"})
    assert result.returncode == 2
    assert "target-skill" in result.stderr
    expected_target = (skill_dir / "enquete" / "sess-2.md").as_posix()
    assert expected_target in result.stderr

    state = state_mod.load_state(state_mod.state_path(tmp_path, "sess-2"))
    assert state["stop_attempts"] == 1


def test_e2e_already_surveyed_skill_allows_stop(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "target-skill"
    enquete_dir = skill_dir / "enquete"
    enquete_dir.mkdir(parents=True)
    (enquete_dir / "sess-3.md").write_text("answered\n", encoding="utf-8")
    _seed_state(tmp_path, "sess-3", {"target-skill": {"dir": str(skill_dir)}})

    result = _run_hook(tmp_path, {"session_id": "sess-3"})
    assert result.returncode == 0, result.stderr


def test_e2e_mixed_surveyed_and_pending_only_lists_pending(tmp_path):
    surveyed_dir = tmp_path / ".claude" / "skills" / "surveyed-skill"
    (surveyed_dir / "enquete").mkdir(parents=True)
    (surveyed_dir / "enquete" / "sess-4.md").write_text("done\n", encoding="utf-8")

    pending_dir = tmp_path / ".claude" / "skills" / "pending-skill"
    pending_dir.mkdir(parents=True)

    _seed_state(
        tmp_path,
        "sess-4",
        {
            "surveyed-skill": {"dir": str(surveyed_dir)},
            "pending-skill": {"dir": str(pending_dir)},
        },
    )

    result = _run_hook(tmp_path, {"session_id": "sess-4"})
    assert result.returncode == 2
    assert "pending-skill" in result.stderr
    assert "surveyed-skill" not in result.stderr


def test_e2e_max_attempts_reached_gives_up(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "target-skill"
    skill_dir.mkdir(parents=True)
    _seed_state(tmp_path, "sess-5", {"target-skill": {"dir": str(skill_dir)}}, stop_attempts=3)

    result = _run_hook(tmp_path, {"session_id": "sess-5"})
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert "target-skill" in output["systemMessage"]

    # Giving up must not keep incrementing stop_attempts forever.
    state = state_mod.load_state(state_mod.state_path(tmp_path, "sess-5"))
    assert state["stop_attempts"] == 3


def test_e2e_stop_hook_active_does_not_bypass_pending_check(tmp_path):
    skill_dir = tmp_path / ".claude" / "skills" / "target-skill"
    skill_dir.mkdir(parents=True)
    _seed_state(tmp_path, "sess-6", {"target-skill": {"dir": str(skill_dir)}})

    result = _run_hook(tmp_path, {"session_id": "sess-6", "stop_hook_active": True})
    assert result.returncode == 2
    assert "target-skill" in result.stderr
