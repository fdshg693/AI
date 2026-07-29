#!/usr/bin/env python3
"""<hooks>
description: /task-tracker <task-name> 呼び出し時に、タスク専用ディレクトリを作成しセッションIDをsessions.mdへ記録する
event: UserPromptExpansion
matcher: ^task-tracker$
hook:
  type: command
  command: python
  args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/task_tracker_session.py"]
</hooks>

UserPromptExpansion hook for the task-tracker skill.

Extracts the task name from `command_args`, creates
`.claude/tasks/{task_name}/` if needed, and appends the current
`session_id` to that directory's `sessions.md`. Never blocks the expansion:
an invalid/missing task name is reported via `additionalContext` only, so
Claude (and the user) notice without the command failing outright.
"""

"""
環境変数（省略可）:
- `HOOK_LOG` このフックの「デバッグログ」（詳細ログ）を`.claude/hooks/logs/task_tracker_session/`に
             書き出すかどうか（true/false等）。フック自体の有効/無効ではない
             （そちらは`.claude/scripts/hooks.yml`の`enabled`で管理する）。
             未設定ならスクリプト先頭の`ENABLE_HOOK_LOG`に従う。
             `.claude/hooks/.env`に設定されていればそちらが優先。
"""
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import hook_log, runtime

# Debug-log ON/OFF only (writes to .claude/hooks/logs/task_tracker_session/) --
# NOT whether this hook itself runs (that's .claude/scripts/hooks.yml's `enabled`).
# `.claude/hooks/.env`'s HOOK_LOG, if set, overrides this default.
ENABLE_HOOK_LOG = False

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

# SKILL.md must apply the same rule when validating $0 itself.
TASK_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def main():
    runtime.configure_utf8_stdio()

    log_enabled = hook_log.is_log_enabled(ENABLE_HOOK_LOG)
    log = {}

    def finish(code, additional_context=None, **extra):
        log.update(extra)
        log["exit_code"] = code
        if log_enabled:
            hook_log.write_log(SCRIPT_NAME, log)
        if additional_context:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptExpansion",
                            "additionalContext": additional_context,
                        }
                    },
                    ensure_ascii=False,
                )
            )
        sys.exit(code)

    payload = runtime.read_json_stdin(finish)

    log["command_name"] = payload.get("command_name")
    log["expansion_type"] = payload.get("expansion_type")

    # Defense in depth: don't rely solely on the <hooks> contract's `matcher`
    # to scope this to /task-tracker. Hyphenated matchers were historically
    # evaluated as unanchored regex on some Claude Code versions (see
    # writing-hooks/hooks.md's matcher pitfalls) and could match unrelated
    # command names; re-check explicitly regardless of what the harness did.
    if payload.get("command_name") != "task-tracker":
        finish(0, reason="command_name is not task-tracker")

    if payload.get("expansion_type") != "slash_command":
        finish(0, reason="not a slash_command expansion")

    command_args = (payload.get("command_args") or "").strip()
    task_name = command_args.split()[0] if command_args else ""
    log["task_name"] = task_name

    if not task_name or not TASK_NAME_RE.match(task_name):
        warning = (
            f"[task-tracker] タスク名 '{task_name}' が不正か空です"
            "（英数字・ハイフン・アンダースコアのみ、先頭は英数字である必要があります）。"
            "セッションIDの記録はスキップされました。ユーザーに正しいタスク名での再実行を促してください。"
        )
        finish(0, additional_context=warning, reason="invalid task name")

    session_id = payload.get("session_id")
    if not session_id:
        finish(0, reason="no session_id in payload")

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    task_dir = os.path.join(project_dir, ".claude", "tasks", task_name)
    os.makedirs(task_dir, exist_ok=True)

    sessions_path = os.path.join(task_dir, "sessions.md")
    is_new = not os.path.exists(sessions_path)

    last_session_id = None
    if not is_new:
        with open(sessions_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
        if lines:
            parts = lines[-1].rsplit(" ", 1)
            if len(parts) == 2:
                last_session_id = parts[1]

    if last_session_id == session_id:
        finish(0, reason="duplicate session_id, not appended", task_dir=task_dir)

    timestamp = datetime.now().astimezone().isoformat()
    with open(sessions_path, "a", encoding="utf-8") as f:
        if is_new:
            f.write(f"# task-tracker sessions: {task_name}\n\n")
        f.write(f"- {timestamp} {session_id}\n")

    finish(0, reason="session recorded", task_dir=task_dir, session_id=session_id)


if __name__ == "__main__":
    main()
