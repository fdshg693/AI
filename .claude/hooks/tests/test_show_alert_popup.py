#!/usr/bin/env python3
"""ポップアップ通知だけの最小テスト（フック／Claude Code 不要）。

使い方（リポジトリルートまたはどこからでも可）:

    python .claude/hooks/tests/test_show_alert_popup.py

期待動作:
- 画面右下に最前面のポップアップウィンドウが表示される
- タイトルバーと本文上部にプロジェクト名（フォルダ名）が表示される
- 既定 300 秒（`STOP_ALERT_POPUP_SECONDS` で変更可）で自動的に閉じる
- クリックすれば即座に閉じられる（Escape／Enter等のキー操作では閉じない）
- このスクリプト自体はポップアップの表示を待たずにすぐ終了する
  （`stop_alert` フックと同じデタッチ挙動の確認を兼ねる）

見た目を確認してから `stop_alert` フックを有効化すると安心。
"""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _lib import show_alert_popup as _show_alert_popup  # noqa: E402


def main() -> int:
    result = _show_alert_popup.show_popup(text="テスト通知です（自動で閉じます）")
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
