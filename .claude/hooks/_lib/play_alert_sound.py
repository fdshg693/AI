#!/usr/bin/env python3
"""Windows向けのアラート音再生ヘルパー（フック本体ではない）。

再生優先順位:
1. 環境変数 `STOP_ALERT_SOUND` で指定されたパス（存在する場合）
2. `.claude/hooks/` 直下の `alert.wav`
3. どちらも無い／再生失敗時はシステムビープ（winsound.MessageBeep）

`alert.wav` はユーザーが後から置く想定。未配置でもビープで動作確認できる。
winsound は WAV のみ対応（MP3 等は不可）。

注意: サウンドスキームが「なし(.None)」だと MessageBeep(MB_ICONASTERISK) は
呼び出しは成功するが音が出ない。そのためレジストリで Asterisk 音が実際に
割り当てられているか確認し、未割り当てなら winsound.Beep() の直接トーン生成へ
フォールバックする（Beep はシステム設定に依存せずスピーカーから音が出る）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# .claude/hooks/_lib/play_alert_sound.py -> _lib -> .claude/hooks (alert.wav lives here)
HOOKS_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SOUND_NAME = "alert.wav"


def resolve_sound_path() -> Path | None:
    """再生対象の WAV パスを返す。無ければ None。"""
    env_path = os.environ.get("STOP_ALERT_SOUND", "").strip()
    if env_path:
        candidate = Path(env_path)
        if candidate.is_file():
            return candidate

    default = HOOKS_DIR / DEFAULT_SOUND_NAME
    if default.is_file():
        return default
    return None


def _system_asterisk_sound_configured() -> bool:
    """Windows の「Asterisk（情報）」システムサウンドが実際に割り当てられているか。

    MessageBeep(MB_ICONASTERISK) は、サウンドスキームで Asterisk が「なし」に
    設定されていると音が出ないのに呼び出しは成功してしまう（戻り値では判別不可）。
    そこでレジストリ HKCU\\AppEvents\\Schemes\\Apps\\.Default\\SystemAsterisk\\.Current
    の値を確認し、空文字列＝「未割り当て」とみなして Beep トーン生成へ逃がす。
    キー不在（ユーザー設定未変更）はスキーム既定に頼るしかないので True 扱い。
    """
    try:
        import winreg
    except ImportError:  # 非 Windows 環境等
        return True  # 判定不能なら従来どおり MessageBeep を試す
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"AppEvents\Schemes\Apps\.Default\SystemAsterisk\.Current",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return bool(value and value.strip())
    except OSError:
        return True


def _play_beep_or_tone() -> dict:
    """システムAsterisk音が割り当てられていれば MessageBeep、無ければ Beep トーン生成。

    Beep(freq, dur) はシステムサウンド設定に依存せず PC のスピーカーから
    直接トーンを鳴らすため、スキーム「なし」でも確実に音が出る。
    MessageBeep が例外で失敗した場合も Beep トーンで逃がす。
    """
    import winsound

    if _system_asterisk_sound_configured():
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return {"ok": True, "mode": "beep", "path": None}
        except Exception as exc:
            try:
                winsound.Beep(880, 300)
                return {
                    "ok": True,
                    "mode": "tone_fallback",
                    "path": None,
                    "detail": str(exc),
                }
            except Exception as tone_exc:
                return {
                    "ok": False,
                    "mode": "beep_failed",
                    "detail": f"{exc}; {tone_exc}",
                }
    # システムサウンド未割り当て: 直接トーン生成
    try:
        winsound.Beep(880, 300)
        return {"ok": True, "mode": "tone", "path": None}
    except Exception as exc:
        return {"ok": False, "mode": "tone_failed", "detail": str(exc)}


def play_alert() -> dict:
    """アラート音を再生する。戻り値は結果の要約（ログ／テスト用）。

    この関数は可能な限り例外を外に出さない。失敗してもフックを壊さない。
    """
    if sys.platform != "win32":
        return {"ok": False, "mode": "unsupported", "detail": f"platform={sys.platform}"}

    try:
        import winsound
    except ImportError as exc:
        return {"ok": False, "mode": "import_error", "detail": str(exc)}

    sound_path = resolve_sound_path()
    if sound_path is not None:
        try:
            # SND_FILENAME: path を WAV として再生 / SND_SYNC: 再生完了まで待つ
            # （プロセス終了で音が途切れるのを防ぐ）
            winsound.PlaySound(
                str(sound_path),
                winsound.SND_FILENAME | winsound.SND_SYNC,
            )
            return {"ok": True, "mode": "file", "path": str(sound_path)}
        except Exception as exc:
            # ファイル破損等でもビープ/トーンへフォールバック
            result = _play_beep_or_tone()
            result = {**result, "path": str(sound_path), "detail": str(exc)}
            return result

    return _play_beep_or_tone()


if __name__ == "__main__":
    # 手動確認用: python .claude/hooks/_lib/play_alert_sound.py
    result = play_alert()
    print(result)
    sys.exit(0 if result.get("ok") else 1)
