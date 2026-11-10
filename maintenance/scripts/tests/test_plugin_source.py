from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugin_meta.util.plugin_source import RemotePlugin, remote_plugin  # noqa: E402


def test_remote_plugin_maps_submodule_paths(tmp_path: Path) -> None:
    (tmp_path / ".gitmodules").write_text(
        '[submodule "tools"]\n\tpath = tools\n\turl = https://github.com/o/AI-tools.git\n'
        '[submodule "skills"]\n\tpath = skills\n\turl = https://github.com/o/AI-skills\n',
        encoding="utf-8",
    )
    assert remote_plugin(tmp_path, "tools/_plugin/my-tools") == RemotePlugin(
        url="https://github.com/o/AI-tools.git", repo="o/AI-tools", path="_plugin/my-tools"
    )
    assert remote_plugin(tmp_path, "skills/plugins/coding") == RemotePlugin(
        url="https://github.com/o/AI-skills.git", repo="o/AI-skills", path="plugins/coding"
    )
    assert remote_plugin(tmp_path, "toolsx/plugin") is None
    assert remote_plugin(tmp_path, "maintenance/plugin") is None


def test_remote_plugin_without_gitmodules(tmp_path: Path) -> None:
    assert remote_plugin(tmp_path, "skills/plugins/coding") is None


def test_remote_plugin_rejects_non_https_github(tmp_path: Path) -> None:
    (tmp_path / ".gitmodules").write_text(
        '[submodule "tools"]\n\tpath = tools\n\turl = git@github.com:o/AI-tools.git\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not an https GitHub URL"):
        remote_plugin(tmp_path, "tools/x")
