"""OpenRouter経由でAIモデルを呼び出すシンプルなCLI（コマンド名: aim）。"""

import argparse
import json
import os
import secrets
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openrouter import OpenRouter
from openrouter.errors import OpenRouterError

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"
LOG_DIR = SCRIPT_DIR / "logs"
UNKNOWN_TRACE_TOOL = "unknown"

# 利用可能なモデル一覧。キーはCLIで指定する略記（元のモデルIDが推測できる形にする）。
MODELS: dict[str, str] = {
    "gpt-120b": "openai/gpt-oss-120b:free",
    "mini-m3": "minimax/minimax-m3",
    "glm-5.2": "z-ai/glm-5.2",
    "gpt-luna": "openai/gpt-5.6-luna",
}

# --web指定時に有効化するOpenRouter Server Tools（モデルが必要と判断した場合のみ呼ばれる）。
WEB_TOOLS: list[dict] = [
    {"type": "openrouter:web_search"},
    {"type": "openrouter:web_fetch"},
]


def print_model_list() -> None:
    width = max(len(alias) for alias in MODELS)
    for alias, model_id in MODELS.items():
        print(f"{alias.ljust(width)}  {model_id}")


def resolve_api_key() -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        return api_key

    load_dotenv(ENV_PATH)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(
            "エラー: OPENROUTER_API_KEY が設定されていません。"
            f"環境変数、または {ENV_PATH} に設定してください。",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def read_prompt(prompt_arg: str | None) -> str:
    if prompt_arg is not None:
        return prompt_arg

    if sys.stdin.isatty():
        print(
            "エラー: プロンプトが指定されていません。"
            "--prompt を指定するか、標準入力から渡してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    prompt = sys.stdin.read().strip()
    if not prompt:
        print("エラー: 標準入力から読み込んだプロンプトが空です。", file=sys.stderr)
        sys.exit(1)
    return prompt


def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(getattr(item, "text", "") or "" for item in content)
    return "" if content is None else str(content)


def _log_path_for(record: dict) -> Path:
    """trace.toolごとのフォルダ、日付ごとのファイルにログを振り分ける。

    trace/trace.toolが空の場合は "unknown" フォルダにまとめる。
    """
    trace = record.get("trace") or {}
    tool = trace.get("tool") or UNKNOWN_TRACE_TOOL
    date = record["timestamp"][:10]
    return LOG_DIR / tool / f"{date}.jsonl"


def append_log(record: dict) -> None:
    log_path = _log_path_for(record)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _new_trace_id() -> str:
    """OTel準拠のtrace id（128bit、32桁hex文字列）を生成する。"""
    return secrets.token_hex(16)


def _resolve_trace(trace: dict[str, str] | None) -> dict[str, str]:
    """trace辞書にtrace_idが無ければ生成して補う（呼び出し元指定のtrace_idは尊重する）。

    ここで確定させたtrace_idはOpenRouterへの送信（Grafana Cloud連携時のTrace ID）と
    ローカルログの両方に使われるため、後からGrafana側のトレースと突き合わせられる。
    """
    resolved = dict(trace) if trace else {}
    resolved.setdefault("trace_id", _new_trace_id())
    return resolved


class AimError(Exception):
    """aim経由のOpenRouter API呼び出しが失敗した場合の例外（openrouterへの依存を隠蔽する）。"""


def create_client(api_key: str | None = None) -> OpenRouter:
    """OpenRouterクライアントを生成する。api_key省略時は resolve_api_key() で解決する。"""
    return OpenRouter(api_key=api_key or resolve_api_key())


def _build_log_record(
    model_id: str,
    prompt: str,
    res,
    *,
    user: str | None = None,
    session_id: str | None = None,
    trace: dict[str, str] | None = None,
) -> dict:
    usage = res.usage
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": model_id,
        "prompt": prompt,
        "cost": usage.cost if usage else None,
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
        "generation_id": res.id,
        "user": user,
        "session_id": session_id,
        "trace": trace,
    }


def call(
    client: OpenRouter,
    model_id: str,
    prompt: str,
    *,
    web: bool = False,
    user: str | None = None,
    session_id: str | None = None,
    trace: dict[str, str] | None = None,
    return_trace_id: bool = False,
) -> str | tuple[str, str]:
    """OpenRouterへの同期呼び出し（薄いラッパー）。呼び出しごとに calls.jsonl へ記録する。

    trace_id未指定時はこの関数がOTel準拠のtrace idを自動生成し、OpenRouterへの送信・
    ログ記録の両方に使う（Grafana Cloud連携時、ローカルログとGrafana側のトレースを
    trace_idで突き合わせられるようにするため）。
    return_trace_id=Trueの場合、戻り値は (応答テキスト, trace_id) のタプルになる。

    ここにログ等を追加すれば、client/call_async 経由の利用者にも同様の挙動が及ぶ。
    """
    trace = _resolve_trace(trace)
    try:
        res = client.chat.send(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            tools=WEB_TOOLS if web else None,
            user=user,
            session_id=session_id,
            trace=trace,
        )
    except OpenRouterError as e:
        raise AimError(str(e)) from e
    append_log(
        _build_log_record(model_id, prompt, res, user=user, session_id=session_id, trace=trace)
    )
    text = extract_text(res.choices[0].message.content)
    return (text, trace["trace_id"]) if return_trace_id else text


async def call_async(
    client: OpenRouter,
    model_id: str,
    prompt: str,
    *,
    web: bool = False,
    user: str | None = None,
    session_id: str | None = None,
    trace: dict[str, str] | None = None,
    return_trace_id: bool = False,
) -> str | tuple[str, str]:
    """OpenRouterへの非同期呼び出し（薄いラッパー）。call() と同じログ処理・trace_id補完を共有する。"""
    trace = _resolve_trace(trace)
    try:
        res = await client.chat.send_async(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            tools=WEB_TOOLS if web else None,
            user=user,
            session_id=session_id,
            trace=trace,
        )
    except OpenRouterError as e:
        raise AimError(str(e)) from e
    append_log(
        _build_log_record(model_id, prompt, res, user=user, session_id=session_id, trace=trace)
    )
    text = extract_text(res.choices[0].message.content)
    return (text, trace["trace_id"]) if return_trace_id else text


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aim", description="OpenRouter経由でAIモデルを呼び出すシンプルなCLI"
    )
    parser.add_argument(
        "--model",
        choices=sorted(MODELS),
        required=False,
        help="利用するモデルの略記（--list-models で一覧表示）",
    )
    parser.add_argument("--prompt", help="プロンプト文字列。省略時は標準入力から読み込む")
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="利用可能なモデルの一覧を表示して終了する",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Web Search/Web Fetch（OpenRouter Server Tools）を有効にする（モデルが必要と判断した場合のみ呼ばれる）",
    )
    args = parser.parse_args()

    if args.list_models:
        print_model_list()
        sys.exit(0)

    if args.model is None:
        parser.error(
            "--model が指定されていません。--list-models で利用可能なモデルを確認してください。"
        )

    model_id = MODELS[args.model]

    prompt = read_prompt(args.prompt)

    try:
        with create_client() as client:
            content = call(client, model_id, prompt, web=args.web, trace={"tool": "aim-cli"})
    except AimError as e:
        print(f"エラー: OpenRouter APIの呼び出しに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"エラー: 予期しないエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)

    print(content)


if __name__ == "__main__":
    main()
