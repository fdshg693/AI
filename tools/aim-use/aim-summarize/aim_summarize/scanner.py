"""対象ファイルの列挙（.gitignore尊重 + 正規表現フィルタ + バイナリ判定）。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath

from aim_summarize.config import Config

BINARY_SNIFF_SIZE = 8192


def list_git_files(repo_root: Path) -> list[str] | None:
    """``repo_root`` 配下で git 管理下にあり、かつ .gitignore で無視されていない全ファイルを
    リポジトリルート相対の POSIX パスで返す。git が使えない/git管理下でない場合は None を返す。
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=repo_root,
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None

    raw = result.stdout.decode("utf-8", errors="surrogateescape")
    return [entry.replace("\\", "/") for entry in raw.split("\0") if entry]


def _matches_include_exclude(rel_path: str, config: Config) -> bool:
    if config.exclude and any(p.search(rel_path) for p in config.exclude):
        return False
    if config.include:
        return any(p.search(rel_path) for p in config.include)
    return True


def to_repo_relative(path: Path, repo_root: Path) -> str | None:
    """``path`` を ``repo_root`` 相対の POSIX パス文字列に変換する。パスの存在は問わない。
    ``repo_root`` の外を指す場合は None を返す。
    """
    try:
        rel = path.resolve().relative_to(repo_root)
    except ValueError:
        return None
    return PurePosixPath(rel.as_posix()).as_posix()


def enumerate_candidate_files(
    repo_root: Path, paths: list[Path] | None, config: Config
) -> list[str]:
    """列挙対象となるリポジトリルート相対パス（POSIX区切り）の一覧を返す。

    ``paths`` が指定された場合はその配下（ファイル/ディレクトリ）に絞り込む。
    """
    git_files = list_git_files(repo_root)
    if git_files is None:
        print(
            "警告: git管理下のリポジトリとして認識できなかったため、.gitignoreを尊重せずに全ファイルを走査します。",
            file=sys.stderr,
        )
        git_files = [to_repo_relative(p, repo_root) for p in repo_root.rglob("*") if p.is_file()]
        git_files = [p for p in git_files if p is not None]

    all_files = sorted(set(git_files))

    if paths:
        rel_scopes: list[str] = []
        for p in paths:
            rel = to_repo_relative(Path(p), repo_root)
            if rel is None:
                print(
                    f"警告: {p} はリポジトリ({repo_root})の外にあるため無視します。",
                    file=sys.stderr,
                )
                continue
            rel_scopes.append(rel)

        def in_scope(rel_path: str) -> bool:
            return any(
                rel_path == scope or rel_path.startswith(scope + "/") for scope in rel_scopes
            )

        all_files = [f for f in all_files if in_scope(f)]

    return [f for f in all_files if _matches_include_exclude(f, config)]


def looks_binary(sample: bytes) -> bool:
    return b"\x00" in sample


def read_text_or_none(path: Path, max_bytes: int) -> tuple[bytes, str] | None:
    """ファイルをバイト列として読み込み、テキストとしてデコードできれば
    ``(raw_bytes, decoded_text)`` を返す。バイナリ判定・デコード失敗時は None を返す。
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    if len(raw) > max_bytes:
        return None

    if looks_binary(raw[:BINARY_SNIFF_SIZE]):
        return None

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None

    return raw, text
