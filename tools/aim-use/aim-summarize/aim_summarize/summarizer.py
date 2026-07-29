"""aim ライブラリ（aim_cli）呼び出し（非同期）+ プロンプト組み立て。"""

from __future__ import annotations

from aim_cli import MODELS, AimError, call_async

PROMPT_TEMPLATE = """\
以下はリポジトリ内のファイル `{file_path}` の内容です。このファイルの要約を日本語で作成してください。

含めるべき観点:
- このファイルの役割・責務
- 主要な関数/クラス/エクスポートとその概要
- 他ファイルとの依存関係で注目すべき点
- 変更時に注意すべき点（あれば）

出力は300〜500文字程度の簡潔な文章または箇条書きでお願いします。コードブロックや前置きは不要です。

---
{file_content}
"""


class SummarizerError(Exception):
    """aim ライブラリ呼び出しが失敗した場合の例外。"""


def build_prompt(file_path: str, file_content: str) -> str:
    return PROMPT_TEMPLATE.format(file_path=file_path, file_content=file_content)


def resolve_model_id(model: str) -> str:
    try:
        return MODELS[model]
    except KeyError as exc:
        available = ", ".join(sorted(MODELS))
        raise SummarizerError(f"未知のモデル {model!r} です。指定可能な値: {available}") from exc


async def _call_once_async(client, model_id: str, prompt: str) -> str:
    try:
        summary = (await call_async(client, model_id, prompt)).strip()
    except AimError as exc:
        raise SummarizerError(f"OpenRouter API呼び出しが失敗しました: {exc}") from exc

    if not summary:
        raise SummarizerError("OpenRouter API の応答が空でした。")
    return summary


async def generate_summary_async(
    client, model_id: str, file_path: str, file_content: str
) -> tuple[bool, str]:
    """要約生成を試みる。失敗時は1回までリトライする。

    戻り値は ``(成功したか, 成功時は要約文字列/失敗時はエラーメッセージ)``。
    """
    prompt = build_prompt(file_path, file_content)
    last_error: str = ""
    for _attempt in range(2):
        try:
            return True, await _call_once_async(client, model_id, prompt)
        except SummarizerError as exc:
            last_error = str(exc)
    return False, last_error
