from __future__ import annotations

from pathlib import Path

import pytest

from skill_deploy.config import load_sets, load_targets
from skill_deploy.models import ConfigError


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_load_sets_missing_file_returns_empty(config_dir: Path) -> None:
    assert load_sets(config_dir) == {}


def test_load_sets_parses_sets(config_dir: Path) -> None:
    write(
        config_dir / "case.yaml",
        """
        sets:
          my-set:
            - a/b
            - c/d/*
        """,
    )
    assert load_sets(config_dir) == {"my-set": ["a/b", "c/d/*"]}


def test_load_sets_rejects_non_mapping_sets(config_dir: Path) -> None:
    write(config_dir / "case.yaml", "sets: not-a-mapping")
    with pytest.raises(ConfigError):
        load_sets(config_dir)


def test_load_sets_rejects_non_string_list_items(config_dir: Path) -> None:
    write(
        config_dir / "case.yaml",
        """
        sets:
          bad-set:
            - 1
            - 2
        """,
    )
    with pytest.raises(ConfigError):
        load_sets(config_dir)


def test_load_targets_merges_multiple_files_sorted_by_name(config_dir: Path) -> None:
    write(
        config_dir / "b-second.yaml",
        """
        targets:
          - dest: dest-b
            items: [item-b]
        """,
    )
    write(
        config_dir / "a-first.yaml",
        """
        targets:
          - dest: dest-a
            items: [item-a]
        """,
    )
    # case.yaml must never be treated as a targets file.
    write(
        config_dir / "case.yaml",
        """
        sets:
          irrelevant: [x]
        """,
    )

    targets = load_targets(config_dir)

    assert [t.dest for t in targets] == ["dest-a", "dest-b"]


def test_load_targets_default_name_uses_file_stem_and_index(config_dir: Path) -> None:
    write(
        config_dir / "vscode.yaml",
        """
        targets:
          - dest: dest-1
            items: [item-1]
          - dest: dest-2
            items: [item-2]
        """,
    )
    targets = load_targets(config_dir)
    assert [t.name for t in targets] == ["vscode#0", "vscode#1"]


def test_load_targets_explicit_name_is_used(config_dir: Path) -> None:
    write(
        config_dir / "vscode.yaml",
        """
        targets:
          - name: my-target
            dest: dest-1
            items: [item-1]
        """,
    )
    targets = load_targets(config_dir)
    assert targets[0].name == "my-target"


@pytest.mark.parametrize(
    "yaml_text",
    [
        "targets: not-a-list",
        "targets:\n  - dest: only-dest-no-items",
        "targets:\n  - items: [x]",
        "targets:\n  - dest: ''\n    items: [x]",
        "targets:\n  - dest: d\n    items: []",
        "targets:\n  - dest: d\n    items: [1, 2]",
        "not-targets-key: []",
    ],
)
def test_load_targets_rejects_malformed_config(config_dir: Path, yaml_text: str) -> None:
    write(config_dir / "bad.yaml", yaml_text)
    if yaml_text == "not-targets-key: []":
        # No `targets` key at all is valid (treated as zero targets), not an error.
        assert load_targets(config_dir) == []
        return
    with pytest.raises(ConfigError):
        load_targets(config_dir)


def test_load_targets_top_level_must_be_mapping(config_dir: Path) -> None:
    write(config_dir / "bad.yaml", "- just-a-list")
    with pytest.raises(ConfigError):
        load_targets(config_dir)
