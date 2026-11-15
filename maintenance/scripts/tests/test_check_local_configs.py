from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check import check_local_configs as clc  # noqa: E402
from check.check_local_configs import Config, LocalConfig  # noqa: E402

CONFIG = Config(
    local_configs=(LocalConfig("tools/aim2/models.json", "tools/aim2/models.json.example"),),
    deny_patterns=("**/settings.json", "**/.env", "**/.env.*", "**/models.json"),
    allow_tracked=(".github/copilot/settings.json",),
)
OK_TRACKED = [
    "README.md",
    "tools",
    "tools/aim2/models.json.example",
    "tools/aim2/.env.example",
    ".github/copilot/settings.json",
]


def ignore_all(paths: list[str]) -> set[str]:
    return set(paths)


def ignore_none(paths: list[str]) -> set[str]:
    return set()


def test_clean_tree_has_no_violations() -> None:
    assert clc.find_violations(CONFIG, OK_TRACKED, ignore_all) == []


def test_declared_real_file_tracked_and_not_ignored() -> None:
    violations = clc.find_violations(CONFIG, [*OK_TRACKED, "tools/aim2/models.json"], ignore_none)
    assert any(v.startswith("tools/aim2/models.json: local config is tracked") for v in violations)
    assert "tools/aim2/models.json: local config is not gitignored" in violations
    # Also caught by the naming rule and the deny pattern.
    assert any("tracked next to its example" in v for v in violations)
    assert any("deny pattern **/models.json" in v for v in violations)


def test_declared_example_missing() -> None:
    tracked = [p for p in OK_TRACKED if not p.endswith("models.json.example")]
    assert clc.find_violations(CONFIG, tracked, ignore_all) == [
        "tools/aim2/models.json.example: example of tools/aim2/models.json is not tracked"
    ]


@pytest.mark.parametrize(
    ("example", "real"),
    [
        ("skills/x/config.example.toml", "skills/x/config.toml"),
        ("skills/x/.diffignore.example", "skills/x/.diffignore"),
        ("agent-compat/formats/a/src.example.md", "agent-compat/formats/a/src.md"),
    ],
)
def test_naming_rule_flags_real_file_next_to_example(example: str, real: str) -> None:
    ok = clc.find_violations(CONFIG, [*OK_TRACKED, example], ignore_all)
    assert ok == []
    violations = clc.find_violations(CONFIG, [*OK_TRACKED, example, real], ignore_all)
    assert f"{real}: tracked next to its example {example}" in violations


def test_deny_pattern_and_allow_tracked() -> None:
    violations = clc.find_violations(
        CONFIG, [*OK_TRACKED, "site/api/settings.json", ".env"], ignore_all
    )
    assert [v.split(":")[0] for v in violations] == [".env", "site/api/settings.json"]


def test_stale_allow_tracked_entry() -> None:
    tracked = [p for p in OK_TRACKED if p != ".github/copilot/settings.json"]
    assert clc.find_violations(CONFIG, tracked, ignore_all) == [
        ".github/copilot/settings.json: listed in allow_tracked but not tracked (remove the entry)"
    ]


def test_example_names() -> None:
    assert clc.is_example_name("settings.example.jsonc")
    assert clc.is_example_name(".env.example")
    assert not clc.is_example_name("example.md")
    assert not clc.is_example_name("examples.json")
    assert clc.real_name("local.settings.example.json") == "local.settings.json"


def test_load_config_rejects_entry_without_reason(tmp_path: Path) -> None:
    path = tmp_path / "local-configs.yaml"
    path.write_text("local_configs:\n  - path: a\n    example: a.example\n", encoding="utf-8")
    with pytest.raises(ValueError, match="reason"):
        clc.load_config(path)


def test_repository_config_loads() -> None:
    config = clc.load_config()
    assert config.local_configs and config.deny_patterns


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "test")
    git(path, "config", "commit.gpgsign", "false")
    git(path, "config", "core.hooksPath", "/dev/null")


def test_check_reads_submodule_index_with_prefix(tmp_path: Path) -> None:
    upstream = tmp_path / "upstream"
    init_repo(upstream)
    (upstream / "models.json.example").write_text("{}\n", encoding="utf-8")
    (upstream / "models.json").write_text("{}\n", encoding="utf-8")
    git(upstream, "add", ".")
    git(upstream, "commit", "-q", "-m", "init")

    root = tmp_path / "umbrella"
    init_repo(root)
    git(root, "submodule", "add", "-q", str(upstream), "tools")
    git(root, "commit", "-q", "-m", "init")

    config = Config(
        local_configs=(LocalConfig("tools/models.json", "tools/models.json.example"),),
        deny_patterns=("**/models.json",),
        allow_tracked=(),
    )
    violations = clc.check(root, config)
    assert "tools/models.json: local config is not gitignored" in violations
    assert any(v.startswith("tools/models.json: local config is tracked") for v in violations)

    sub = root / "tools"
    git(sub, "rm", "-q", "--cached", "models.json")
    (sub / ".gitignore").write_text("models.json\n", encoding="utf-8")
    git(sub, "add", ".gitignore")
    assert clc.check(root, config) == []
