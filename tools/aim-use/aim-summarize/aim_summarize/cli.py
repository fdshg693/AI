"""``aim-summarize`` のエントリポイント。argparse: generate / get サブコマンド。"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aim_cli import create_client

from aim_summarize import formatter
from aim_summarize.config import load_config_or_exit
from aim_summarize.db import SummaryDB
from aim_summarize.hasher import hash_bytes
from aim_summarize.scanner import enumerate_candidate_files, read_text_or_none, to_repo_relative
from aim_summarize.summarizer import SummarizerError, generate_summary_async, resolve_model_id

JST = timezone(timedelta(hours=9))


def now_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def _row_to_entry(row) -> formatter.SummaryEntry:
    return {
        "file_path": row["file_path"],
        "summary": row["summary"],
        "model": row["model"],
        "generated_at": row["generated_at"],
        "content_hash": row["content_hash"],
    }


def _missing_entry(file_path: str) -> formatter.SummaryEntry:
    return {
        "file_path": file_path,
        "summary": None,
        "model": None,
        "generated_at": None,
        "content_hash": None,
    }


async def _generate_all_async(
    model_id: str, jobs: int, new_or_changed: list[tuple[str, str, str]]
) -> list[tuple[str, str, bool, str]]:
    """新規/変更ファイルの要約を並行生成する（単一プロセス内、スレッド不使用）。

    戻り値は各ファイルについて ``(rel_path, content_hash, 成功したか, 要約/エラーメッセージ)``。
    """
    semaphore = asyncio.Semaphore(jobs)

    async def worker(client, rel_path: str, text: str, content_hash: str):
        async with semaphore:
            success, result = await generate_summary_async(client, model_id, rel_path, text)
        return rel_path, content_hash, success, result

    async with create_client() as client:
        return await asyncio.gather(
            *(
                worker(client, rel_path, text, content_hash)
                for rel_path, text, content_hash in new_or_changed
            )
        )


def cmd_generate(args: argparse.Namespace) -> int:
    config = load_config_or_exit(Path.cwd())
    try:
        model_id = resolve_model_id(config.model)
    except SummarizerError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    paths = [Path(p) for p in args.paths] if args.paths else None
    candidate_files = enumerate_candidate_files(config.repo_root, paths, config)

    new_or_changed: list[tuple[str, str, str]] = []  # (rel_path, text, content_hash)
    unchanged: list[str] = []
    too_large: list[str] = []
    binary_or_encoding_error: list[str] = []

    with SummaryDB(config.db_path) as db:
        for rel_path in candidate_files:
            full_path = config.repo_root / rel_path
            try:
                size = full_path.stat().st_size
            except OSError:
                continue

            if size > config.max_file_size_bytes:
                too_large.append(rel_path)
                if not args.dry_run:
                    db.record_skip(
                        rel_path,
                        "too_large",
                        f"{size} bytes > {config.max_file_size_bytes} bytes",
                        now_iso(),
                    )
                continue

            result = read_text_or_none(full_path, config.max_file_size_bytes)
            if result is None:
                binary_or_encoding_error.append(rel_path)
                if not args.dry_run:
                    db.record_skip(rel_path, "binary_or_encoding_error", None, now_iso())
                continue

            raw, text = result
            content_hash = hash_bytes(raw)
            existing_hash = None if args.force else db.get_content_hash(rel_path)
            if existing_hash == content_hash:
                unchanged.append(rel_path)
                continue

            new_or_changed.append((rel_path, text, content_hash))

        if args.dry_run:
            _print_dry_run_summary(new_or_changed, unchanged, too_large, binary_or_encoding_error)
            return 0

        generated = 0
        failed = 0
        results = asyncio.run(_generate_all_async(model_id, config.jobs, new_or_changed))
        for rel_path, content_hash, success, result in results:
            if success:
                db.upsert_summary(rel_path, content_hash, result, config.model, now_iso())
                generated += 1
            else:
                db.record_skip(rel_path, "generation_failed", result, now_iso())
                failed += 1

        removed = 0
        for known_path in db.all_known_file_paths():
            if not (config.repo_root / known_path).exists():
                db.delete_file(known_path)
                removed += 1

        _print_generate_summary(
            generated=generated,
            unchanged=len(unchanged),
            too_large=len(too_large),
            binary_or_encoding_error=len(binary_or_encoding_error),
            generation_failed=failed,
            removed=removed,
        )

    return 0


def _print_dry_run_summary(
    new_or_changed: list[tuple[str, str, str]],
    unchanged: list[str],
    too_large: list[str],
    binary_or_encoding_error: list[str],
) -> None:
    def section(title: str, files: list[str]) -> None:
        print(f"[dry-run] {title}: {len(files)}件")
        for f in files:
            print(f"  {f}")

    section("新規生成/再生成", [rel_path for rel_path, _text, _hash in new_or_changed])
    section("維持（変更なし）", unchanged)
    section("スキップ(too_large)", too_large)
    section("スキップ(binary_or_encoding_error)", binary_or_encoding_error)


def _print_generate_summary(
    *,
    generated: int,
    unchanged: int,
    too_large: int,
    binary_or_encoding_error: int,
    generation_failed: int,
    removed: int,
) -> None:
    print(f"生成: {generated}件")
    print(f"維持: {unchanged}件")
    print(f"スキップ(too_large): {too_large}件")
    print(f"スキップ(binary_or_encoding_error): {binary_or_encoding_error}件")
    print(f"スキップ(generation_failed): {generation_failed}件")
    print(f"孤立レコード削除: {removed}件")


def cmd_get(args: argparse.Namespace) -> int:
    config = load_config_or_exit(Path.cwd())

    with SummaryDB(config.db_path) as db:
        entries: list[formatter.SummaryEntry] = []
        if not args.paths:
            entries = [_row_to_entry(row) for row in db.get_all_summaries()]
        else:
            seen: set[str] = set()
            for raw_path in args.paths:
                rel = to_repo_relative(Path(raw_path), config.repo_root)
                if rel is None:
                    print(
                        f"警告: {raw_path} はリポジトリ({config.repo_root})の外にあるため無視します。",
                        file=sys.stderr,
                    )
                    continue
                rows = db.get_summaries_under(rel)
                if rows:
                    for row in rows:
                        if row["file_path"] not in seen:
                            seen.add(row["file_path"])
                            entries.append(_row_to_entry(row))
                else:
                    if rel not in seen:
                        seen.add(rel)
                        entries.append(_missing_entry(rel))

    if args.format == "json":
        print(formatter.format_json(entries))
    else:
        print(formatter.format_markdown(entries))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aim-summarize",
        description="aim CLI を基盤としたリポジトリファイル要約ツール",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="ファイル要約を生成・更新する")
    generate_parser.add_argument("paths", nargs="*", help="対象パス（省略時はリポジトリ全体）")
    generate_parser.add_argument(
        "--force", action="store_true", help="ハッシュ一致でも対象全件を再生成する"
    )
    generate_parser.add_argument(
        "--dry-run", action="store_true", help="実際には生成せず、対象件数と一覧のみ表示する"
    )
    generate_parser.set_defaults(func=cmd_generate)

    get_parser = subparsers.add_parser("get", help="DBから要約を取得する")
    get_parser.add_argument("paths", nargs="*", help="対象パス（省略時はDB全件）")
    get_parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown", help="出力フォーマット"
    )
    get_parser.set_defaults(func=cmd_get)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
