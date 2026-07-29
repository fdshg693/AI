"""解決済みのコピー元パスを配置先へ実際にコピーする（フォルダでもファイルでもよい）。"""

from __future__ import annotations

import shutil
from pathlib import Path

IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__", "*.pyc", ".pytest_cache", "*.egg-info", ".env"
)


def copy_item(source: Path, dest_dir: Path, *, dry_run: bool) -> str:
    """``source`` を ``dest_dir/<source.name>`` へコピーする。

    既存のフォルダ・ファイルは削除してから配置し直す（クリーンコピー）。
    ``dry_run=True`` の場合はファイルシステムに触れず、実行予定の内容を文字列で返すだけ。
    """
    target = dest_dir / source.name

    if source.is_dir():
        description = f"{source} -> {target}/"
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target, ignore=IGNORE_PATTERNS)
        return description

    description = f"{source} -> {target}"
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return description
