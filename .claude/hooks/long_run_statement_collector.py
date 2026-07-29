#!/usr/bin/env python3
"""<hooks>
description: ターン終了時(Stop)にセッショントランスクリプトから今回のターンで新たに生成されたアシスタント発言（テキスト）を抽出し、長時間実行監視の収集ログに記録するフックの設定。このフック自体はナッジ判定（加重操作量・失敗連続回数の閾値監視）には一切関与せず、常にブロックせず素通りする（そちらは`long_run_collector.py`が担う）。価値はナッジ機構そのものではなく、`long_run_collector.py`が記録するツール呼び出しログに発言テキストを時系列で並記し、事後調査（暴走・迷走したセッションの原因究明、ログ要約）に使える完全な操作トレイルを完成させる点にある。単体では地味に見えるが、単独の効果ではなく他フックと合わせたログ全体への寄与で評価すること。
event: Stop
hook:
  type: command
  command: python
  args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/long_run_statement_collector.py"]
</hooks>

Stop hook that records "what Claude said to the user" into the same
collection log `long_run_collector.py` (registered for both `PostToolUse`
and `PostToolUseFailure`) writes tool calls to
(`.claude/hooks/state/long_run/<timestamp>-<session_id>.jsonl`, `type: "statement"`).

There is no per-message hook event for assistant text (only `PreToolUse`/
`PostToolUse` fire per tool call), so this reads the session transcript
(`transcript_path` from the hook payload) instead, scanning only the lines
past `transcript_offset` (persisted in the shared state file) so repeated
Stop firings in the same session never re-log the same statement twice.

Never blocks the turn (always exits 0, regardless of outcome) and honors
`stop_hook_active` to avoid doing pointless re-work if Claude Code re-fires
this Stop hook for an unrelated reason (e.g. another Stop hook blocking).
This hook does not participate in the operation-count/nudge threshold at
all -- that's `_lib.long_run_state.record_and_maybe_nudge()`, driven only
by tool calls.
"""

"""
環境変数（省略可）:
- `HOOK_LOG` このフックの「デバッグログ」を`.claude/hooks/logs/long_run_statement_collector/`に
             書き出すかどうか（true/false等）。フック自体の有効/無効ではない
             （そちらは`.claude/scripts/hooks.yml`の`enabled`で管理する）。
             未設定ならスクリプト先頭の`ENABLE_HOOK_LOG`に従う。
             `.claude/hooks/.env`に設定されていればそちらが優先。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import runtime
from _lib import long_run_state as state_mod

# Debug-log ON/OFF only (writes to .claude/hooks/logs/long_run_statement_collector/) --
# NOT whether this hook itself runs (that's .claude/scripts/hooks.yml's `enabled`).
# `.claude/hooks/.env`'s HOOK_LOG, if set, overrides this default.
ENABLE_HOOK_LOG = False

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]


def extract_assistant_texts(transcript_path, start_line):
    """Return (texts, new_line_count) for assistant text blocks in lines
    `[start_line, end)` of the transcript jsonl. Unparsable/missing lines
    and non-text content are skipped, never raised -- a corrupt transcript
    should never break the Stop hook."""
    texts = []
    line_count = start_line
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for i, raw in enumerate(f):
                if i < start_line:
                    continue
                line_count = i + 1
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                content = (obj.get("message") or {}).get("content") or []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text")
                        if isinstance(text, str) and text.strip():
                            texts.append(text)
    except OSError:
        return texts, start_line
    return texts, line_count


def main():
    payload, log, finish = runtime.init_hook_context(SCRIPT_NAME, ENABLE_HOOK_LOG)

    if payload.get("stop_hook_active"):
        finish(0, reason="stop_hook_active, skipping")

    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")
    log["session_id"] = session_id
    if not session_id or not transcript_path:
        finish(0, reason="missing session_id/transcript_path")

    project_dir = state_mod.resolve_project_dir()
    state_file, log_file = state_mod.session_paths(project_dir, session_id)

    state = state_mod.load_state(state_file)
    texts, new_offset = extract_assistant_texts(transcript_path, state["transcript_offset"])

    for text in texts:
        state_mod.append_log(log_file, {"type": "statement", "text": text})

    state["transcript_offset"] = new_offset
    state_mod.save_state(state_file, state)

    finish(0, reason="recorded", statements=len(texts))


if __name__ == "__main__":
    main()
