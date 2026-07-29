from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """テスト用の使い捨てリポジトリルート。中身は各テストが必要に応じて作る。"""
    root = tmp_path / "repo"
    root.mkdir()
    return root


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    config = tmp_path / "config"
    config.mkdir()
    return config
