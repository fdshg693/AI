#!/usr/bin/env python3
"""<hooks>
description: Claudeの応答完了（Stop）時にWindowsでアラート音を鳴らすフックの設定
event: Stop
hook:
  type: command
  command: python
  args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/stop_alert.py"]
  timeout: 15
</hooks>

Stop hook that plays an alert sound when Claude finishes a turn.

On Windows, plays `.claude/hooks/alert.wav` if present (or the path in
`STOP_ALERT_SOUND`); otherwise falls back to a system beep. Never blocks
the stop (always exits 0). Honors `stop_hook_active` to avoid Stop-hook
re-entry loops even though this hook does not block.

音声ファイルの単体確認は `.claude/hooks/tests/test_play_alert_sound.py` を使う。
"""

"""
環境変数（省略可）:
- `STOP_ALERT_SOUND`  再生する WAV の絶対／相対パス。未設定なら
                      `.claude/hooks/alert.wav` を探し、無ければシステムビープ。
- `HOOK_LOG`          このフックの「デバッグログ」を`.claude/hooks/logs/stop_alert/`
                      に書き出すかどうか（true/false等）。フック自体の有効/無効ではない
                      （そちらは`.claude/scripts/hooks.yml`の`enabled`で管理する）。
                      未設定ならスクリプト先頭の`ENABLE_HOOK_LOG`に従う。
                      `.claude/hooks/.env`に設定されていればそちらが優先。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import hook_log, play_alert_sound, runtime

# Debug-log ON/OFF only (writes to .claude/hooks/logs/stop_alert/) --
# NOT whether this hook itself runs (that's .claude/scripts/hooks.yml's `enabled`).
# `.claude/hooks/.env`'s HOOK_LOG, if set, overrides this default.
ENABLE_HOOK_LOG = False

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]


def main():
    runtime.configure_utf8_stdio()

    log_enabled = hook_log.is_log_enabled(ENABLE_HOOK_LOG)
    log = {}
    finish = runtime.make_finish(SCRIPT_NAME, log, log_enabled)

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # stdin が空／壊れていても音だけは鳴らす（手動テストやパイプ漏れ対策）
        payload = {}
        log["stdin"] = "unparsable"

    # Stop フックが自分自身を再トリガーしている最中は何もしない（無限ループ回避）
    if payload.get("stop_hook_active"):
        finish(0, reason="stop_hook_active, skipped")

    result = play_alert_sound.play_alert()
    finish(0, reason="played", sound=result)


if __name__ == "__main__":
    main()
