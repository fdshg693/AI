#!/usr/bin/env python3
"""アラート音再生だけの最小テスト（フック／Claude Code 不要）。

使い方（リポジトリルートまたはどこからでも可）:

    python .claude/hooks/tests/test_play_alert_sound.py

期待動作:
- `.claude/hooks/alert.wav` があればそれを再生
- 無ければ Windows のシステムビープ
- 終了コード 0 = 再生成功、1 = 失敗

音声ファイルを置いたあと、このスクリプトで音が出ることを確認してから
`stop_alert` フックを有効化すると安心。
"""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _lib import play_alert_sound as _play_alert_sound  # noqa: E402


def main() -> int:
    sound = _play_alert_sound.resolve_sound_path()
    if sound is not None:
        print(f"sound file: {sound}")
    else:
        print(
            "sound file: (none) — "
            f"place {HOOKS_DIR / _play_alert_sound.DEFAULT_SOUND_NAME} "
            "or set STOP_ALERT_SOUND; falling back to system beep"
        )

    result = _play_alert_sound.play_alert()
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
