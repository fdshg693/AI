#!/usr/bin/env python3
"""<hooks>
description: 全ツール呼び出し（成功）を長時間実行監視の収集ログに記録し、加重操作量（成功+1・失敗+3）や失敗連続回数が閾値に達したら状況確認・サブエージェント検討を促す固定メッセージをClaudeへ返すフックの設定
event: PostToolUse
matcher: "*"
hook:
  type: command
  command: python
  args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/long_run_collector.py"]
</hooks>
<hooks>
description: 全ツール呼び出し（失敗）を長時間実行監視の収集ログに記録し、加重操作量（成功+1・失敗+3）や失敗連続回数が閾値に達したら状況確認・サブエージェント検討を促す固定メッセージをClaudeへ返すフックの設定
event: PostToolUseFailure
matcher: "*"
hook:
  type: command
  command: python
  args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/long_run_collector.py"]
</hooks>

Single script registered for both `PostToolUse` and `PostToolUseFailure`
(see `hooks_manager.py`'s support for multiple `<hooks>` blocks in one
docstring) -- this replaces what used to be two near-duplicate scripts
(`long_run_collector.py` + `long_run_collector_failure.py`), which only
differed in which event they were registered for; all actual logic already
lived in `_lib/long_run_state.py`. Which event fired is read from
`hook_event_name` in the payload: `"PostToolUseFailure"` means the call
failed, anything else (including a missing field, this hook's fail-open
policy) is treated as success.

Every tool call is appended to this session's collection log
(`.claude/hooks/state/long_run/<timestamp>-<session_id>.jsonl`) and folded into two
per-session counters (see `_lib/long_run_state.py` for the actual policy):

- `weighted_count`: +1 per success, +3 per failure. `AskUserQuestion`
  resets it to zero instead of adding to it -- the counter tracks "weighted
  operations since the agent last checked in with the user". Reaching
  `LONG_RUN_OP_THRESHOLD` (default 30) resets it to zero and nudges.
- `failure_streak`: consecutive tool-call failures; any success (or
  `AskUserQuestion`) resets it to zero. Reaching
  `LONG_RUN_FAILURE_STREAK_THRESHOLD` (default 3) resets it to zero and
  nudges -- this is the signal for "stuck retrying the same failing command
  in a loop", which `weighted_count` alone would also eventually catch, but
  only much later.

Both thresholds can trigger on the same call; when they do, both nudge
messages are concatenated into one `reason` (see
`_lib.long_run_state.nudge_message()`). `PostToolUse`/`PostToolUseFailure`
can't undo the tool call that already ran, but `decision: "block"` still
delivers the `reason` text to Claude as feedback it can act on -- that's the
whole mechanism here, not an attempt to revert anything.

Never fails closed: missing `tool_name`/`session_id` just skips recording.
"""

"""
環境変数（省略可）:
- `LONG_RUN_OP_THRESHOLD` 加重操作量（成功+1・失敗+3）がAskUserQuestionなしで
                          いくつに達したらナッジを送るか（デフォルト: 30）。
- `LONG_RUN_FAILURE_STREAK_THRESHOLD` ツール呼び出しの失敗が連続何回続いたら
                          ナッジを送るか（デフォルト: 3）。
- `HOOK_LOG` このフックの「デバッグログ」を`.claude/hooks/logs/long_run_collector/`に
             書き出すかどうか（true/false等）。フック自体の有効/無効ではない
             （そちらは`.claude/scripts/hooks.yml`の`enabled`で管理する）。
             未設定ならスクリプト先頭の`ENABLE_HOOK_LOG`に従う。
             `.claude/hooks/.env`に設定されていればそちらが優先。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import runtime
from _lib import long_run_state as state_mod

# Debug-log ON/OFF only (writes to .claude/hooks/logs/long_run_collector/) --
# NOT whether this hook itself runs (that's .claude/scripts/hooks.yml's `enabled`).
# `.claude/hooks/.env`'s HOOK_LOG, if set, overrides this default.
ENABLE_HOOK_LOG = False

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
DEFAULT_WEIGHTED_THRESHOLD = 30
DEFAULT_FAILURE_STREAK_THRESHOLD = 3


def main():
    payload, log, finish = runtime.init_hook_context(SCRIPT_NAME, ENABLE_HOOK_LOG)

    tool_name = payload.get("tool_name")
    session_id = payload.get("session_id")
    log["tool_name"] = tool_name
    if not tool_name or not session_id:
        finish(0, reason="no tool_name/session_id in payload")

    success = payload.get("hook_event_name") != "PostToolUseFailure"
    log["success"] = success

    project_dir = state_mod.resolve_project_dir()
    weighted_threshold = runtime.env_int("LONG_RUN_OP_THRESHOLD", DEFAULT_WEIGHTED_THRESHOLD)
    failure_streak_threshold = runtime.env_int(
        "LONG_RUN_FAILURE_STREAK_THRESHOLD", DEFAULT_FAILURE_STREAK_THRESHOLD
    )
    tool_input = payload.get("tool_input") or {}

    weighted_count, failure_streak, nudge = state_mod.record_and_maybe_nudge(
        project_dir,
        session_id,
        tool_name,
        tool_input,
        success=success,
        weighted_threshold=weighted_threshold,
        failure_streak_threshold=failure_streak_threshold,
    )
    log["weighted_count"] = weighted_count
    log["failure_streak"] = failure_streak

    if nudge is None:
        finish(0, reason="recorded")

    output = {"decision": "block", "reason": nudge}
    finish(0, output=output, reason="threshold reached, nudge sent")


if __name__ == "__main__":
    main()
