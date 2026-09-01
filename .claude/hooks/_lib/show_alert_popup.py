#!/usr/bin/env python3
"""Windows向けのポップアップ通知ヘルパー（フック本体ではない）。

Stopフックの音（`play_alert_sound.py`）だけでは、サウンド設定（消音・
スキーム未設定等）によっては気づけないことがある。より確実に気づける
手段として、画面右下に最前面のポップアップウィンドウを表示する。

tkinterのmainloopは自プロセスをブロックするため、`show_popup()` は
このファイル自身を別プロセス（デタッチ）として起動するだけで即座に
戻る。フック本体の応答（Stop処理）を待たせない。

環境変数（省略可）:
- `STOP_ALERT_POPUP`          ポップアップを出すかどうか。未設定なら true。
                              `.claude/hooks/.env`での指定にも対応（`hook_log.resolve_bool_flag`経由）。
- `STOP_ALERT_POPUP_SECONDS`  自動で閉じるまでの秒数。未設定なら 6。
- `STOP_ALERT_POPUP_TEXT`     表示メッセージ。未設定なら既定文言。

手動確認: `.claude/hooks/tests/test_show_alert_popup.py` を参照。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import hook_log

DEFAULT_TEXT = "Claude Codeの応答が完了しました"
DEFAULT_SECONDS = 300.0


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def show_popup(text: str | None = None, seconds: float | None = None) -> dict:
    """ポップアップをデタッチした別プロセスで表示する（呼び出し元をブロックしない）。

    この関数は可能な限り例外を外に出さない。失敗してもフックを壊さない。
    """
    if sys.platform != "win32":
        return {"ok": False, "mode": "unsupported", "detail": f"platform={sys.platform}"}

    if not hook_log.resolve_bool_flag("STOP_ALERT_POPUP", True):
        return {"ok": False, "mode": "disabled"}

    message = text or os.environ.get("STOP_ALERT_POPUP_TEXT", "").strip() or DEFAULT_TEXT
    duration = (
        seconds if seconds is not None else _env_float("STOP_ALERT_POPUP_SECONDS", DEFAULT_SECONDS)
    )

    try:
        # DETACHED_PROCESS: 親（このフック）のコンソール/終了から独立させる
        # CREATE_NEW_PROCESS_GROUP: Ctrl+C 等のシグナルを親から引き継がない
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), message, str(duration)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
        )
        return {"ok": True, "mode": "spawned", "text": message, "seconds": duration}
    except Exception as exc:
        return {"ok": False, "mode": "spawn_failed", "detail": str(exc)}


def _run_window(text: str, seconds: float) -> None:
    """実際にポップアップを描画する（このファイルを子プロセスとして起動した側の本体）。"""
    import tkinter as tk

    root = tk.Tk()
    root.title("Claude Code")
    root.attributes("-topmost", True)
    try:
        root.attributes("-toolwindow", True)
    except tk.TclError:
        pass

    label = tk.Label(
        root,
        text=text,
        font=("Segoe UI", 12),
        padx=24,
        pady=18,
        justify="left",
        wraplength=360,
    )
    label.pack()

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    margin = 24
    x = max(screen_width - width - margin, 0)
    y = max(screen_height - height - margin - 48, 0)  # タスクバー分を避ける
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.bind("<Button-1>", lambda _event: root.destroy())
    root.bind("<Escape>", lambda _event: root.destroy())
    root.bind("<Return>", lambda _event: root.destroy())
    root.after(max(int(seconds * 1000), 500), root.destroy)

    root.mainloop()


if __name__ == "__main__":
    # 手動確認 / 実際の表示プロセスの本体:
    #   python .claude/hooks/_lib/show_alert_popup.py "テスト" 5
    _text = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEXT
    _seconds = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SECONDS
    _run_window(_text, _seconds)
