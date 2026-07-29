"""既定のリポジトリルート・設定ディレクトリを計算する。"""

from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def default_repo_root() -> Path:
    """``integrations/scripts/skill_deploy/`` から3階層上 = リポジトリルート。"""
    return _PACKAGE_DIR.parents[2]


def default_config_dir() -> Path:
    """``integrations/scripts/config/``。"""
    return _PACKAGE_DIR.parent / "config"
