"""``skill-deploy`` のエントリポイント。

``config/`` 配下の設定に従い、リポジトリ内のスキル等のフォルダ/ファイルを複数の配置先へコピーする。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skill_deploy.config import load_sets, load_targets
from skill_deploy.copier import copy_item
from skill_deploy.models import ConfigError, ResolvedCopy, ResolveError, Target
from skill_deploy.paths import default_config_dir, default_repo_root
from skill_deploy.resolver import resolve_target


def collect(
    config_dir: Path, repo_root: Path
) -> tuple[list[Target], list[ResolvedCopy], list[str]]:
    """全設定ファイルを読み込み、ターゲット一覧・解決済みコピー一覧・警告一覧を返す。"""
    sets = load_sets(config_dir)
    targets = load_targets(config_dir)

    copies: list[ResolvedCopy] = []
    warnings: list[str] = []
    for target in targets:
        target_copies, target_warnings = resolve_target(target, sets, repo_root)
        copies.extend(target_copies)
        warnings.extend(target_warnings)

    return targets, copies, warnings


def filter_by_only(
    targets: list[Target], copies: list[ResolvedCopy], only: list[str] | None
) -> tuple[list[ResolvedCopy], list[str]]:
    """``--only`` で指定されたターゲット名だけに絞り込む。戻り値は ``(絞り込み後, 未知の名前一覧)``。"""
    if not only:
        return copies, []

    only_set = set(only)
    valid_names = {t.name for t in targets}
    unknown = sorted(n for n in only_set if n not in valid_names)
    if unknown:
        return [], unknown

    return [c for c in copies if c.target_name in only_set], []


def _print_grouped(copies: list[ResolvedCopy], *, dry_run: bool) -> None:
    current_target: str | None = None
    for copy in copies:
        if copy.target_name != current_target:
            current_target = copy.target_name
            print(f"[{current_target}]")
        description = copy_item(copy.source, copy.dest_dir, dry_run=dry_run)
        prefix = "  [dry-run] " if dry_run else "  "
        print(f"{prefix}{description}")


def _run(args: argparse.Namespace, *, dry_run: bool) -> int:
    repo_root = args.repo_root.resolve() if args.repo_root else default_repo_root()
    config_dir = args.config_dir.resolve() if args.config_dir else default_config_dir()

    try:
        targets, copies, warnings = collect(config_dir, repo_root)
    except (ConfigError, ResolveError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    filtered, unknown = filter_by_only(targets, copies, args.only)
    if unknown:
        print(f"エラー: 未知のターゲット名です: {', '.join(unknown)}", file=sys.stderr)
        available = ", ".join(sorted({t.name for t in targets})) or "(なし)"
        print(f"利用可能なターゲット: {available}", file=sys.stderr)
        return 1

    if not filtered:
        print("コピー対象がありません。")
    else:
        _print_grouped(filtered, dry_run=dry_run)

    for warning in warnings:
        print(f"警告: {warning}", file=sys.stderr)

    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    return _run(args, dry_run=True)


def cmd_apply(args: argparse.Namespace) -> int:
    return _run(args, dry_run=False)


def cmd_list_sets(args: argparse.Namespace) -> int:
    config_dir = args.config_dir.resolve() if args.config_dir else default_config_dir()

    try:
        sets = load_sets(config_dir)
    except ConfigError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    if not sets:
        print(f"セットは定義されていません ({config_dir / 'case.yaml'})")
        return 0

    for name, items in sets.items():
        print(f"@{name}:")
        for item in items:
            print(f"  - {item}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-deploy",
        description="config/ の設定に従い、リポジトリ内のスキル等のフォルダ/ファイルを複数の配置先へコピーするCLI",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=None,
        help="設定ファイル(config/*.yaml)を置くディレクトリ。省略時は integrations/scripts/config",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="コピー元パス・相対destの基準ディレクトリ。省略時はこのリポジトリのルート",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="実際にはコピーせず、コピー計画を表示する")
    plan_parser.add_argument(
        "--only", action="append", help="このターゲット名だけを対象にする(複数指定可)"
    )
    plan_parser.set_defaults(func=cmd_plan)

    apply_parser = subparsers.add_parser("apply", help="設定に従って実際にコピーを実行する")
    apply_parser.add_argument(
        "--only", action="append", help="このターゲット名だけを対象にする(複数指定可)"
    )
    apply_parser.set_defaults(func=cmd_apply)

    list_sets_parser = subparsers.add_parser(
        "list-sets", help="case.yaml に定義済みのセット一覧を表示する"
    )
    list_sets_parser.set_defaults(func=cmd_list_sets)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
