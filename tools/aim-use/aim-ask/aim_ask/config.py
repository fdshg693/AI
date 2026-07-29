"""``.aim-use/aim-ask.toml`` の探索・読み込み（省略可。見つからない場合は組み込みデフォルトを使う）。"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from aim_ask.asker import DEFAULT_PROMPT
from aim_cli import MODELS

CONFIG_DIR_NAME = ".aim-use"
CONFIG_FILE_NAME = "aim-ask.toml"

DEFAULT_MODEL = "mini-m3"
DEFAULT_JOBS = 4

JOBS_MIN = 1
JOBS_MAX = 10


class ConfigError(Exception):
    """設定ファイルの読み込み・バリデーションに失敗した場合の例外。"""


@dataclass
class AskConfig:
    prompt: str
    model: str
    jobs: int


def find_config_path(start: Path) -> Path | None:
    """``start`` から親方向に ``.aim-use/aim-ask.toml`` を探索する。見つからなければ None。"""
    current = start.resolve()
    for candidate in (current, *current.parents):
        config_path = candidate / CONFIG_DIR_NAME / CONFIG_FILE_NAME
        if config_path.is_file():
            return config_path
    return None


def _validate_prompt(raw: object) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ConfigError(f"prompt は空でない文字列で指定してください: {raw!r}")
    return raw


def _validate_model(raw: object) -> str:
    if raw not in MODELS:
        allowed = ", ".join(sorted(MODELS))
        raise ConfigError(f"model の値が不正です: {raw!r}。指定可能な値: {allowed}")
    return raw


def _validate_jobs(raw: object) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise ConfigError(f"jobs は整数で指定してください: {raw!r}")
    if not (JOBS_MIN <= raw <= JOBS_MAX):
        raise ConfigError(f"jobs は{JOBS_MIN}〜{JOBS_MAX}の範囲で指定してください: {raw!r}")
    return raw


def load_config(start: Path) -> AskConfig:
    """設定ファイルが見つかればその値で上書きし、見つからなければ組み込みデフォルトを返す。"""
    config = AskConfig(prompt=DEFAULT_PROMPT, model=DEFAULT_MODEL, jobs=DEFAULT_JOBS)

    config_path = find_config_path(start)
    if config_path is None:
        return config

    try:
        with config_path.open("rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{config_path} の TOML 構文が不正です: {exc}") from exc

    if "prompt" in raw:
        config.prompt = _validate_prompt(raw["prompt"])
    if "model" in raw:
        config.model = _validate_model(raw["model"])
    if "jobs" in raw:
        config.jobs = _validate_jobs(raw["jobs"])

    return config


def load_config_or_exit(start: Path) -> AskConfig:
    try:
        return load_config(start)
    except ConfigError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
