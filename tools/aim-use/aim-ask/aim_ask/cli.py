"""``aim-ask`` のエントリポイント。複数ファイルへ同一プロンプトを並列に投げるCLI。"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

from aim_cli import MODELS, create_client

from aim_ask.asker import AskerError, ask_file_async, resolve_model_id
from aim_ask.config import JOBS_MAX, JOBS_MIN, load_config_or_exit
from aim_ask.formatter import ResultEntry, format_json, format_markdown

BINARY_SNIFF_SIZE = 8192
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
}


def resolve_path(raw_path: str, cwd: Path) -> Path:
    """相対パスは ``cwd`` 基準で解決し、``..`` 等を正規化した絶対パスを返す。"""
    p = Path(raw_path)
    return (p if p.is_absolute() else cwd / p).resolve()


def read_text_or_error(
    path: Path, full_content_names: set[str] | None = None
) -> tuple[str | None, str | None]:
    """戻り値は ``(ファイル内容, None)`` または ``(None, エラーメッセージ)``。

    ``full_content_names`` はディレクトリ入力時のみ使う。指定した場合、
    ディレクトリ配下のうちファイル名がこの集合に含まれるものだけ内容を含め、
    それ以外はツリー listing 上のパスのみになる（内容は渡さない）。
    """
    if not path.exists():
        return None, f"パスが存在しません: {path}"
    if path.is_dir():
        return _format_directory_text(path, full_content_names), None

    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"ファイルの読み込みに失敗しました: {exc}"

    if b"\x00" in raw[:BINARY_SNIFF_SIZE]:
        return None, "バイナリファイルのため対象外です。"

    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "UTF-8としてデコードできませんでした。"


async def _run_all_async(
    model_id: str, prompt: str, jobs: int, targets: list[tuple[int, str, str]], session_id: str
) -> list[tuple[int, bool, str]]:
    """対象ファイルへのAI呼び出しを並行実行する（単一プロセス内、スレッド不使用）。

    ``targets`` は ``(entries内でのindex, パス文字列, ファイル内容)`` のリスト。
    戻り値は各要素について ``(index, 成功したか, 応答/エラーメッセージ)``。
    """
    semaphore = asyncio.Semaphore(jobs)

    async def worker(client, idx: int, raw_path: str, text: str):
        async with semaphore:
            success, result = await ask_file_async(
                client,
                model_id,
                prompt,
                text,
                session_id=session_id,
                trace={"tool": "aim-ask", "file_path": raw_path},
            )
        return idx, success, result

    async with create_client() as client:
        return await asyncio.gather(
            *(worker(client, idx, raw_path, text) for idx, raw_path, text in targets)
        )


def cmd_ask(args: argparse.Namespace) -> int:
    config = load_config_or_exit(Path.cwd())

    prompt = args.prompt if args.prompt is not None else config.prompt
    model_alias = args.model if args.model is not None else config.model
    jobs = args.jobs if args.jobs is not None else config.jobs

    if not (JOBS_MIN <= jobs <= JOBS_MAX):
        print(
            f"エラー: --jobs は{JOBS_MIN}〜{JOBS_MAX}の範囲で指定してください: {jobs}",
            file=sys.stderr,
        )
        return 1

    try:
        model_id = resolve_model_id(model_alias)
    except AskerError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    full_content_names: set[str] | None = None
    if args.full_content_names is not None:
        full_content_names = {
            name.strip() for name in args.full_content_names.split(",") if name.strip()
        }

    cwd = Path.cwd()
    entries: list[ResultEntry] = []
    targets: list[tuple[int, str, str]] = []
    for raw_path in args.paths:
        resolved = resolve_path(raw_path, cwd)
        text, error = read_text_or_error(resolved, full_content_names)
        entries.append(
            {
                "path": raw_path,
                "resolved_path": str(resolved),
                "success": False,
                "response": None,
                "error": error,
            }
        )
        if text is not None:
            targets.append((len(entries) - 1, raw_path, text))

    if targets:
        session_id = str(uuid.uuid4())
        results = asyncio.run(_run_all_async(model_id, prompt, jobs, targets, session_id))
        for idx, success, result in results:
            entries[idx]["success"] = success
            if success:
                entries[idx]["response"] = result
            else:
                entries[idx]["error"] = result

    if args.format == "json":
        print(format_json(entries))
    else:
        print(format_markdown(entries))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aim-ask",
        description="複数ファイルまたはディレクトリへ同一プロンプトを並列に投げ、パスと応答の対応付きで結果を返すCLI",
    )
    parser.add_argument(
        "paths", nargs="+", help="対象ファイルまたはディレクトリパス（相対パスはCWD基準で解決）"
    )
    parser.add_argument(
        "--prompt", help="AIに渡すプロンプト文字列。省略時は設定ファイル/組み込みデフォルトを使用"
    )
    parser.add_argument(
        "--model",
        choices=sorted(MODELS),
        help="利用するモデルの略記。省略時は設定ファイル/組み込みデフォルトを使用",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        help=f"並列実行数（{JOBS_MIN}〜{JOBS_MAX}）。省略時は設定ファイル/組み込みデフォルトを使用",
    )
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown", help="出力フォーマット"
    )
    parser.add_argument(
        "--full-content-names",
        help=(
            "ディレクトリ入力時、内容を含めるファイル名のカンマ区切り指定（例: SKILL.md,README.md）。"
            "省略時は配下の全ファイル内容を含める（従来どおり）。指定した場合、"
            "一致しないファイルはツリー listing のパスのみになり内容は渡さない"
        ),
    )
    parser.set_defaults(func=cmd_ask)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


def _collect_directory_entries(path: Path) -> tuple[list[tuple[Path, bool]], list[Path]]:
    """除外ディレクトリを省いて、ツリー表示用のパスとファイル一覧を集める。"""
    entries: list[tuple[Path, bool]] = []
    files: list[Path] = []

    for root, directory_names, file_names in os.walk(path, topdown=True):
        directory_names[:] = sorted(
            name for name in directory_names if name not in EXCLUDED_DIRECTORY_NAMES
        )
        for name in directory_names:
            entries.append((Path(root) / name, True))
        for name in sorted(file_names):
            file_path = Path(root) / name
            entries.append((file_path, False))
            files.append(file_path)

    return entries, files


def _format_directory_text(path: Path, full_content_names: set[str] | None = None) -> str:
    """ディレクトリのツリー listing と各ファイル内容を1つの文字列にする。

    ``full_content_names`` を指定した場合、ファイル名がこの集合に含まれるものだけ
    内容を含め、それ以外はツリー listing 上のパスのみ（内容なし）にする。
    """
    entries, files = _collect_directory_entries(path)
    file_contents: dict[tuple[str, ...], str] = {}
    file_errors: dict[tuple[str, ...], str] = {}
    file_filtered: set[tuple[str, ...]] = set()
    tree_children: dict[tuple[str, ...], list[tuple[str, bool]]] = {(): []}

    for entry_path, is_directory in entries:
        relative_parts = entry_path.relative_to(path).parts
        parent_parts = relative_parts[:-1]
        tree_children.setdefault(parent_parts, []).append((relative_parts[-1], is_directory))
        if is_directory:
            tree_children.setdefault(relative_parts, [])

    for file_path in files:
        relative_parts = file_path.relative_to(path).parts
        if full_content_names is not None and file_path.name not in full_content_names:
            file_filtered.add(relative_parts)
            continue
        content, error = read_text_or_error(file_path)
        if content is not None:
            file_contents[relative_parts] = content
        else:
            file_errors[relative_parts] = error or "読み込めませんでした。"

    def render_tree(parent_parts: tuple[str, ...], prefix: str) -> list[str]:
        children = sorted(
            tree_children.get(parent_parts, []), key=lambda item: (not item[1], item[0])
        )
        lines: list[str] = []
        for index, (name, is_directory) in enumerate(children):
            is_last = index == len(children) - 1
            connector = "└──" if is_last else "├──"
            child_parts = parent_parts + (name,)
            note = ""
            if not is_directory and child_parts in file_errors:
                note = f" [読み込みスキップ: {file_errors[child_parts]}]"
            elif not is_directory and child_parts in file_filtered:
                note = " [内容省略（対象外ファイル）]"
            lines.append(f"{prefix}{connector} {name}{note}")
            if is_directory:
                child_prefix = prefix + ("    " if is_last else "│   ")
                lines.extend(render_tree(child_parts, child_prefix))
        return lines

    sections = ["ディレクトリツリー:", ".", *render_tree((), "")]
    for relative_parts, content in sorted(file_contents.items()):
        relative_path = "/".join(relative_parts)
        sections.extend([f"\n--- FILE: {relative_path} ---", content])
    return "\n".join(sections)


if __name__ == "__main__":
    main()
