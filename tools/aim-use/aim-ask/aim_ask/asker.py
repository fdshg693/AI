"""aim ライブラリ（aim_cli）呼び出し（非同期）。プロンプトはファイル単位で変化しない。"""

from __future__ import annotations

from aim_cli import MODELS, AimError, call_async

DEFAULT_PROMPT = """\
以下のファイル内容を日本語で要約してください。

含めるべき観点:
- このファイルの役割・責務
- 主要な要素（関数/クラス/エクスポート等）とその概要
- 変更時に注意すべき点（あれば）

出力は300〜500文字程度の簡潔な文章または箇条書きでお願いします。コードブロックや前置きは不要です。\
"""


class AskerError(Exception):
    """aim ライブラリ呼び出しが失敗した場合の例外。"""


def build_message(prompt: str, file_content: str) -> str:
    """全ファイル共通の ``prompt`` にファイル内容を付加した、AIへの最終メッセージを組み立てる。

    ``prompt`` 自体はどのファイルに対しても同一の文字列であり、ファイルパスは埋め込まない。
    """
    return f"{prompt}\n\n---\n{file_content}"


def resolve_model_id(model: str) -> str:
    try:
        return MODELS[model]
    except KeyError as exc:
        available = ", ".join(sorted(MODELS))
        raise AskerError(f"未知のモデル {model!r} です。指定可能な値: {available}") from exc


async def _call_once_async(client, model_id: str, message: str) -> str:
    try:
        response = (await call_async(client, model_id, message)).strip()
    except AimError as exc:
        raise AskerError(f"OpenRouter API呼び出しが失敗しました: {exc}") from exc

    if not response:
        raise AskerError("OpenRouter API の応答が空でした。")
    return response


async def ask_file_async(client, model_id: str, prompt: str, file_content: str) -> tuple[bool, str]:
    """1ファイル分のAI呼び出しを試みる。失敗時は1回までリトライする。

    戻り値は ``(成功したか, 成功時は応答文字列/失敗時はエラーメッセージ)``。
    """
    message = build_message(prompt, file_content)
    last_error: str = ""
    for _attempt in range(2):
        try:
            return True, await _call_once_async(client, model_id, message)
        except AskerError as exc:
            last_error = str(exc)
    return False, last_error
