#!/usr/bin/env python3
"""Windows向けのポップアップ通知ヘルパー（フック本体ではない）。

Stopフックの音（`play_alert_sound.py`）だけでは、サウンド設定（消音・
スキーム未設定等）によっては気づけないことがある。より確実に気づける
手段として、画面右下に最前面のポップアップウィンドウを表示する。

tkinterのmainloopは自プロセスをブロックするため、`show_popup()` は
このファイル自身を別プロセス（デタッチ）として起動するだけで即座に
戻る。フック本体の応答（Stop処理）を待たせない。

複数フォルダ（複数のClaude Codeセッション）を同時に動かしていると、
どのプロジェクトからの通知か判別できないため、`_resolve_project_title()`
で解決したプロジェクト名をタイトルバーとポップアップ本文の両方に出す
（優先順位は同関数のdocstring参照: `CLAUDE_PROJECT_DIR`env var → git →
`.claude`フォルダを辿る → "unknown"）。

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

DEFAULT_TEXT = "Claude Codeの応答が完了しました"
DEFAULT_SECONDS = 300.0
UNKNOWN_PROJECT_TITLE = "unknown"


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _resolve_project_title() -> str:
    """どのプロジェクトが発火したポップアップかを表すフォルダ名を解決する。

    複数フォルダ（複数のClaude Codeセッション）を同時に動かしていると、
    タイトルが無いと通知がどのプロジェクトのものか判別できない。優先順位:

    1. `CLAUDE_PROJECT_DIR` 環境変数 -- Claude Codeがフックプロセスに必ず
       設定する（公式ドキュメント確認済み）。フックが発火したセッションの
       `.claude/settings.json` を含むプロジェクトルートそのものなので、これが
       最も正確。
    2. `git rev-parse --show-toplevel` -- 手動実行など env 変数が無い場合の
       Gitリポジトリルート。
    3. このファイル自身の場所から上位ディレクトリを辿り、`.claude` フォルダが
       見つかったらその親フォルダ名（envもgitも使えない最後の砦）。
    4. どれも失敗したら "unknown"。

    例外を外に出さない（失敗してもポップアップ自体は表示する）。
    """
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if env_dir:
        name = Path(env_dir).name
        if name:
            return name

    try:
        git_creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=git_creationflags,
        )
        if result.returncode == 0:
            name = Path(result.stdout.strip()).name
            if name:
                return name
    except Exception:
        pass

    try:
        for ancestor in Path(__file__).resolve().parents:
            if (ancestor / ".claude").is_dir():
                return ancestor.name
    except Exception:
        pass

    return UNKNOWN_PROJECT_TITLE


def show_popup(text: str | None = None, seconds: float | None = None) -> dict:
    """ポップアップをデタッチした別プロセスで表示する（呼び出し元をブロックしない）。

    この関数は可能な限り例外を外に出さない。失敗してもフックを壊さない。
    """
    if sys.platform != "win32":
        return {"ok": False, "mode": "unsupported", "detail": f"platform={sys.platform}"}

    # ここでのみ相対importするのは、このモジュール自身が `__main__` として
    # （＝下の子プロセスとして）直接起動されたとき、モジュールレベルの相対
    # importだと "no known parent package" で即クラッシュするため。
    from . import hook_log

    if not hook_log.resolve_bool_flag("STOP_ALERT_POPUP", True):
        return {"ok": False, "mode": "disabled"}

    message = text or os.environ.get("STOP_ALERT_POPUP_TEXT", "").strip() or DEFAULT_TEXT
    duration = (
        seconds if seconds is not None else _env_float("STOP_ALERT_POPUP_SECONDS", DEFAULT_SECONDS)
    )
    project_title = _resolve_project_title()

    try:
        # CREATE_NO_WINDOW: コンソールウィンドウを一切作らない。DETACHED_PROCESS
        # だけだと、Windows 11の既定ターミナル機構が新規コンソール要求を検知して
        # 新しいWindows Terminal（PowerShell）ウィンドウを前面に出してしまうため、
        # DETACHED_PROCESSではなくこちらを使う。
        # CREATE_NEW_PROCESS_GROUP: Ctrl+C 等のシグナルを親から引き継がない
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                message,
                str(duration),
                project_title,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
        )
        return {
            "ok": True,
            "mode": "spawned",
            "text": message,
            "seconds": duration,
            "project": project_title,
        }
    except Exception as exc:
        return {"ok": False, "mode": "spawn_failed", "detail": str(exc)}


def _run_window(text: str, seconds: float, project_title: str) -> None:
    """実際にポップアップを描画する（このファイルを子プロセスとして起動した側の本体）。"""
    import tkinter as tk

    root = tk.Tk()
    root.title(f"Claude Code - {project_title}")
    root.attributes("-topmost", True)
    try:
        root.attributes("-toolwindow", True)
    except tk.TclError:
        pass

    frame = tk.Frame(root, padx=24, pady=18)
    frame.pack()

    tk.Label(
        frame,
        text=project_title,
        font=("Segoe UI", 10, "bold"),
        justify="left",
        anchor="w",
    ).pack(fill="x")

    tk.Label(
        frame,
        text=text,
        font=("Segoe UI", 12),
        justify="left",
        anchor="w",
        wraplength=360,
    ).pack(fill="x", pady=(4, 0))

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    margin = 24
    x = max(screen_width - width - margin, 0)
    y = max(screen_height - height - margin - 48, 0)  # タスクバー分を避ける
    root.geometry(f"{width}x{height}+{x}+{y}")

    # ユーザーが明示的にクリックしない限り、時間制限いっぱいまで表示し続ける
    # （Escape/Enter等のキー操作では閉じない）。
    root.bind("<Button-1>", lambda _event: root.destroy())
    root.after(max(int(seconds * 1000), 500), root.destroy)

    root.mainloop()


if __name__ == "__main__":
    # 手動確認 / 実際の表示プロセスの本体:
    #   python .claude/hooks/_lib/show_alert_popup.py "テスト" 5 my-project
    _text = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEXT
    _seconds = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SECONDS
    _project_title = sys.argv[3] if len(sys.argv) > 3 else _resolve_project_title()
    _run_window(_text, _seconds, _project_title)
