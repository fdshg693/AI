"""``items:`` の各エントリ（``@set`` 参照 / glob / 単一パス）をコピー元パスへ解決する。"""

from __future__ import annotations

import os
from pathlib import Path

from skill_deploy.models import ResolvedCopy, ResolveError, Target

GLOB_CHARS = ("*", "?", "[")


def _is_glob(item: str) -> bool:
    return any(ch in item for ch in GLOB_CHARS)


def expand_item(
    item: str,
    sets: dict[str, list[str]],
    repo_root: Path,
    _set_stack: tuple[str, ...] = (),
) -> tuple[list[Path], list[str]]:
    """1つの ``items`` エントリを解決する。戻り値は ``(パス一覧, 警告一覧)``。"""
    if item.startswith("@"):
        set_name = item[1:]
        if set_name not in sets:
            raise ResolveError(f"未定義のセットです: @{set_name}")
        if set_name in _set_stack:
            chain = " -> ".join([*_set_stack, set_name])
            raise ResolveError(f"セットの循環参照を検出しました: {chain}")

        paths: list[Path] = []
        warnings: list[str] = []
        for sub_item in sets[set_name]:
            sub_paths, sub_warnings = expand_item(
                sub_item, sets, repo_root, (*_set_stack, set_name)
            )
            paths.extend(sub_paths)
            warnings.extend(sub_warnings)
        return paths, warnings

    if _is_glob(item):
        matches = sorted(repo_root.glob(item))
        warnings = [] if matches else [f"パターンに一致するファイルがありません: {item}"]
        return matches, warnings

    resolved = repo_root / item
    if not resolved.exists():
        raise ResolveError(f"パスが存在しません: {item} (repo_root={repo_root})")
    return [resolved], []


def resolve_dest(raw: str, repo_root: Path) -> Path:
    """``~`` と環境変数を展開し、相対パスなら ``repo_root`` 基準で絶対パス化する。"""
    expanded = os.path.expanduser(os.path.expandvars(raw))
    path = Path(expanded)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def resolve_target(
    target: Target,
    sets: dict[str, list[str]],
    repo_root: Path,
) -> tuple[list[ResolvedCopy], list[str]]:
    """1つの ``Target`` を解決済みコピー一覧と警告一覧に変換する。"""
    dest_dir = resolve_dest(target.dest, repo_root)

    copies: list[ResolvedCopy] = []
    warnings: list[str] = []
    seen: set[Path] = set()

    for item in target.items:
        try:
            paths, item_warnings = expand_item(item, sets, repo_root)
        except ResolveError as exc:
            raise ResolveError(f"{target.source_file} のターゲット '{target.name}': {exc}") from exc

        warnings.extend(f"[{target.name}] {w}" for w in item_warnings)

        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            copies.append(ResolvedCopy(target_name=target.name, dest_dir=dest_dir, source=path))

    return copies, warnings
