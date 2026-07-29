"""``config/`` 配下の設定ファイル群を読み込む。

- ``case.yaml``: ``@name`` で参照できる名前付きセット (`sets:`) を定義する特別なファイル。
- それ以外の ``*.yaml`` / ``*.yml``: 配置先 (`targets:`) を定義する。1ファイルに複数の配置先を
  書いてもよいし、好きな粒度でファイルを分割してもよい（全ファイルをマージして扱う）。
"""

from __future__ import annotations

from pathlib import Path

import yaml

from skill_deploy.models import ConfigError, Target

CASE_FILE_NAMES = ("case.yaml", "case.yml")


def _load_yaml(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"{path} を読み込めません: {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} のYAML構文が不正です: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: トップレベルはマッピングである必要があります")
    return data


def _config_files(config_dir: Path) -> list[Path]:
    files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))
    return sorted(files, key=lambda p: p.name)


def load_sets(config_dir: Path) -> dict[str, list[str]]:
    """``case.yaml`` の ``sets:`` を読み込む。ファイルが無ければ空の辞書を返す。"""
    for name in CASE_FILE_NAMES:
        case_path = config_dir / name
        if case_path.is_file():
            break
    else:
        return {}

    data = _load_yaml(case_path)
    raw_sets = data.get("sets", {})
    if not isinstance(raw_sets, dict):
        raise ConfigError(f"{case_path}: sets はマッピングで指定してください")

    sets: dict[str, list[str]] = {}
    for set_name, items in raw_sets.items():
        if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
            raise ConfigError(f"{case_path}: sets.{set_name} は文字列のリストで指定してください")
        sets[str(set_name)] = list(items)
    return sets


def load_targets(config_dir: Path) -> list[Target]:
    """``case.yaml`` 以外の ``*.yaml``/``*.yml`` から ``targets:`` を集めてマージする。"""
    targets: list[Target] = []

    for path in _config_files(config_dir):
        if path.name in CASE_FILE_NAMES:
            continue

        data = _load_yaml(path)
        raw_targets = data.get("targets", [])
        if not isinstance(raw_targets, list):
            raise ConfigError(f"{path}: targets はリストで指定してください")

        for i, raw in enumerate(raw_targets):
            if not isinstance(raw, dict):
                raise ConfigError(f"{path}: targets[{i}] はマッピングである必要があります")

            dest = raw.get("dest")
            if not isinstance(dest, str) or not dest.strip():
                raise ConfigError(f"{path}: targets[{i}].dest は空でない文字列で指定してください")

            items = raw.get("items")
            if (
                not isinstance(items, list)
                or not items
                or not all(isinstance(i, str) for i in items)
            ):
                raise ConfigError(
                    f"{path}: targets[{i}].items は1件以上の文字列のリストで指定してください"
                )

            name = raw.get("name", f"{path.stem}#{i}")
            if not isinstance(name, str) or not name.strip():
                raise ConfigError(f"{path}: targets[{i}].name は空でない文字列で指定してください")

            targets.append(Target(name=name, dest=dest, items=items, source_file=path))

    return targets
