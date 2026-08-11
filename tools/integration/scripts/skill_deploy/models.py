"""設定ファイルをパースした結果を保持するデータ構造。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """``config/*.yaml`` の読み込み・構文検証に失敗した場合の例外。"""


class ResolveError(Exception):
    """``@set`` 参照やソースパスの解決に失敗した場合の例外。"""


@dataclass
class Target:
    """1つのコピー先（``dest``）と、そこへ配置する項目一覧（``items``）。"""

    name: str
    dest: str
    items: list[str]
    source_file: Path


@dataclass
class ResolvedCopy:
    """解決済みの「このソースをこの1階層下へコピーする」という単位。"""

    target_name: str
    dest_dir: Path
    source: Path
