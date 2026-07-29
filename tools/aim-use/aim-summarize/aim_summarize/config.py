"""``.aim-use/config.toml`` の読み込み・バリデーション。"""

from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from aim_cli import MODELS

CONFIG_DIR_NAME = ".aim-use"
CONFIG_FILE_NAME = "config.toml"
DB_FILE_NAME = "summaries.db"

DEFAULT_MODEL = "mini-m3"
DEFAULT_JOBS = 4
DEFAULT_MAX_FILE_SIZE_BYTES = 204800

JOBS_MIN = 2
JOBS_MAX = 10


class ConfigError(Exception):
    """設定ファイルの読み込み・バリデーションに失敗した場合の例外。"""


@dataclass
class Config:
    repo_root: Path
    config_path: Path
    db_path: Path
    model: str
    jobs: int
    max_file_size_bytes: int
    include: list[re.Pattern[str]]
    exclude: list[re.Pattern[str]]


def find_repo_root(start: Path) -> Path:
    """``start`` から親方向に ``.aim-use/config.toml`` を探索し、見つかったディレクトリを返す。"""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / CONFIG_DIR_NAME / CONFIG_FILE_NAME).is_file():
            return candidate
    raise ConfigError(
        f"{CONFIG_DIR_NAME}/{CONFIG_FILE_NAME} が見つかりませんでした。"
        f"{start} から親ディレクトリを遡って探索しましたが見つかりません。"
        f"対象リポジトリのルートに {CONFIG_DIR_NAME}/{CONFIG_FILE_NAME} を作成してください"
        "（config.toml.example をコピーして利用できます）。"
    )


def _compile_patterns(raw_entries: object, key: str) -> list[re.Pattern[str]]:
    if raw_entries is None:
        return []
    if not isinstance(raw_entries, list):
        raise ConfigError(f"[[{key}]] はテーブルの配列で指定してください。")

    patterns: list[re.Pattern[str]] = []
    for entry in raw_entries:
        if not isinstance(entry, dict) or "pattern" not in entry:
            raise ConfigError(f"[[{key}]] の各要素には pattern キーが必要です。")
        pattern = entry["pattern"]
        if not isinstance(pattern, str):
            raise ConfigError(f"[[{key}]].pattern は文字列で指定してください。")
        try:
            patterns.append(re.compile(pattern))
        except re.error as exc:
            raise ConfigError(
                f"[[{key}]].pattern の正規表現が不正です: {pattern!r} ({exc})"
            ) from exc
    return patterns


def load_config(repo_root: Path) -> Config:
    config_path = repo_root / CONFIG_DIR_NAME / CONFIG_FILE_NAME
    try:
        with config_path.open("rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{config_path} の TOML 構文が不正です: {exc}") from exc

    model = raw.get("model", DEFAULT_MODEL)
    if model not in MODELS:
        allowed = ", ".join(sorted(MODELS))
        raise ConfigError(f"model の値が不正です: {model!r}。指定可能な値: {allowed}")

    jobs = raw.get("jobs", DEFAULT_JOBS)
    if not isinstance(jobs, int) or isinstance(jobs, bool):
        raise ConfigError(f"jobs は整数で指定してください: {jobs!r}")
    if not (JOBS_MIN <= jobs <= JOBS_MAX):
        raise ConfigError(f"jobs は{JOBS_MIN}〜{JOBS_MAX}の範囲で指定してください: {jobs!r}")

    max_file_size_bytes = raw.get("max_file_size_bytes", DEFAULT_MAX_FILE_SIZE_BYTES)
    if (
        not isinstance(max_file_size_bytes, int)
        or isinstance(max_file_size_bytes, bool)
        or max_file_size_bytes <= 0
    ):
        raise ConfigError(
            f"max_file_size_bytes は正の整数で指定してください: {max_file_size_bytes!r}"
        )

    include = _compile_patterns(raw.get("include"), "include")
    exclude = _compile_patterns(raw.get("exclude"), "exclude")

    return Config(
        repo_root=repo_root,
        config_path=config_path,
        db_path=repo_root / CONFIG_DIR_NAME / DB_FILE_NAME,
        model=model,
        jobs=jobs,
        max_file_size_bytes=max_file_size_bytes,
        include=include,
        exclude=exclude,
    )


def load_config_or_exit(start: Path) -> Config:
    try:
        repo_root = find_repo_root(start)
        return load_config(repo_root)
    except ConfigError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
