#!/usr/bin/env python3
"""`inject_env_vars.py`（PreToolUse hook）のテスト。

使い方（リポジトリルートから）:

    uv run pytest .claude/hooks/tests/test_inject_env_vars.py

パース系・値解決系の関数は直接importして単体テストし、実際のフック起動時の
挙動（tool_name判定・override時の既存環境変数チェック・JSON出力の形）は
サブプロセスとして起動し、独立した一時プロジェクトディレクトリ
（`CLAUDE_PROJECT_DIR`）に対してエンドツーエンドで検証する。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import inject_env_vars as hook  # noqa: E402

SCRIPT_PATH = HOOKS_DIR / "inject_env_vars.py"


# ---------------------------------------------------------------------------
# parse_env_yaml
# ---------------------------------------------------------------------------


def test_parse_env_yaml_literal_values_and_default_override():
    override, env_vars = hook.parse_env_yaml(
        """
        vars:
          FOO: bar
          BAZ: "quoted value"
          QUX: 'single quoted'
        """.replace("        ", "")
    )
    assert override is False
    assert env_vars == {"FOO": "bar", "BAZ": "quoted value", "QUX": "single quoted"}


def test_parse_env_yaml_override_true_variants():
    for truthy in ("true", "True", "yes", "1", "on"):
        override, _ = hook.parse_env_yaml(f"override: {truthy}\nvars:\n  FOO: bar\n")
        assert override is True, truthy

    for falsy in ("false", "no", "0", "off", ""):
        override, _ = hook.parse_env_yaml(f"override: {falsy}\nvars:\n  FOO: bar\n")
        assert override is False, falsy


def test_parse_env_yaml_ignores_comments_and_blank_lines():
    text = """
# top comment
override: false

vars:
  # a comment inside vars
  FOO: bar

  BAZ: qux
"""
    override, env_vars = hook.parse_env_yaml(text)
    assert override is False
    assert env_vars == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_yaml_duplicate_nested_keys_last_wins():
    text = "vars:\n  FOO: first\n  FOO: second\n"
    _, env_vars = hook.parse_env_yaml(text)
    assert env_vars == {"FOO": "second"}


def test_parse_env_yaml_duplicate_top_level_keys_last_wins():
    text = "override: false\noverride: true\nvars:\n  FOO: bar\n"
    override, _ = hook.parse_env_yaml(text)
    assert override is True


def test_parse_env_yaml_duplicate_vars_blocks_last_wins():
    text = "vars:\n  FOO: first\nvars:\n  FOO: second\n  BAR: baz\n"
    _, env_vars = hook.parse_env_yaml(text)
    assert env_vars == {"FOO": "second", "BAR": "baz"}


def test_parse_env_yaml_value_containing_colon():
    text = "vars:\n  DATABASE_URL: postgres://user:pass@host/db\n"
    _, env_vars = hook.parse_env_yaml(text)
    assert env_vars == {"DATABASE_URL": "postgres://user:pass@host/db"}


def test_parse_env_yaml_at_reference_value_is_kept_verbatim():
    text = 'vars:\n  SECRET: "@secrets/local.env"\n'
    _, env_vars = hook.parse_env_yaml(text)
    assert env_vars == {"SECRET": "@secrets/local.env"}


def test_parse_env_yaml_no_vars_section():
    override, env_vars = hook.parse_env_yaml("override: true\n")
    assert override is True
    assert env_vars == {}


# ---------------------------------------------------------------------------
# _load_dotenv_value
# ---------------------------------------------------------------------------


def test_load_dotenv_value_found(tmp_path):
    p = tmp_path / "local.env"
    p.write_text('# comment\nFOO=bar\nBAZ="qux"\n', encoding="utf-8")
    assert hook._load_dotenv_value(p, "FOO") == "bar"
    assert hook._load_dotenv_value(p, "BAZ") == "qux"


def test_load_dotenv_value_missing_key(tmp_path):
    p = tmp_path / "local.env"
    p.write_text("FOO=bar\n", encoding="utf-8")
    assert hook._load_dotenv_value(p, "NOPE") is None


def test_load_dotenv_value_missing_file(tmp_path):
    assert hook._load_dotenv_value(tmp_path / "nope.env", "FOO") is None


def test_load_dotenv_value_duplicate_keys_last_wins(tmp_path):
    p = tmp_path / "local.env"
    p.write_text("FOO=first\nFOO=second\n", encoding="utf-8")
    assert hook._load_dotenv_value(p, "FOO") == "second"


# ---------------------------------------------------------------------------
# resolve_value
# ---------------------------------------------------------------------------


def test_resolve_value_literal_passthrough(tmp_path):
    warnings = []
    assert hook.resolve_value("FOO", "bar", tmp_path, warnings) == "bar"
    assert warnings == []


def test_resolve_value_at_reference_success(tmp_path):
    (tmp_path / "secrets").mkdir()
    (tmp_path / "secrets" / "local.env").write_text("FOO=resolved\n", encoding="utf-8")
    warnings = []
    result = hook.resolve_value("FOO", "@secrets/local.env", tmp_path, warnings)
    assert result == "resolved"
    assert warnings == []


def test_resolve_value_at_reference_missing_key_warns(tmp_path):
    (tmp_path / "secrets").mkdir()
    (tmp_path / "secrets" / "local.env").write_text("OTHER=x\n", encoding="utf-8")
    warnings = []
    result = hook.resolve_value("FOO", "@secrets/local.env", tmp_path, warnings)
    assert result is None
    assert len(warnings) == 1
    assert "FOO" in warnings[0]


def test_resolve_value_at_reference_missing_file_warns(tmp_path):
    warnings = []
    result = hook.resolve_value("FOO", "@secrets/nope.env", tmp_path, warnings)
    assert result is None
    assert len(warnings) == 1


# ---------------------------------------------------------------------------
# build_export_prefix
# ---------------------------------------------------------------------------


def test_build_export_prefix_bash_escapes_single_quotes():
    prefix = hook.build_export_prefix("Bash", {"FOO": "it's a test"})
    assert prefix == "export FOO='it'\\''s a test'"


def test_build_export_prefix_powershell_escapes_single_quotes():
    prefix = hook.build_export_prefix("PowerShell", {"FOO": "it's a test"})
    assert prefix == "$env:FOO='it''s a test'"


def test_build_export_prefix_multiple_vars_preserves_order():
    prefix = hook.build_export_prefix("Bash", {"A": "1", "B": "2"})
    assert prefix == "export A='1'\nexport B='2'"


# ---------------------------------------------------------------------------
# End-to-end: run the hook as a subprocess against a sandboxed project dir
# ---------------------------------------------------------------------------


def _make_project(tmp_path):
    """Build a throwaway `CLAUDE_PROJECT_DIR` with just enough of `.claude/`
    to exercise the hook exactly as it runs in a real repo, without touching
    this repo's own files."""
    project = tmp_path / "project"
    hooks_dir = project / ".claude" / "hooks"
    config_dir = hooks_dir / "config"
    config_dir.mkdir(parents=True)
    shutil.copy(SCRIPT_PATH, hooks_dir / "inject_env_vars.py")
    shutil.copytree(HOOKS_DIR / "_lib", hooks_dir / "_lib")
    return project, config_dir


def _run_hook(project, tool_name, command, extra_env=None):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env.pop("HOOK_LOG", None)
    env.pop("NOTIFY_INJECTED_VARS", None)
    if extra_env:
        env.update(extra_env)
    payload = json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(project / ".claude" / "hooks" / "inject_env_vars.py")],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return result


def test_e2e_no_config_is_noop(tmp_path):
    project, _ = _make_project(tmp_path)
    result = _run_hook(project, "Bash", "echo hi")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_e2e_non_command_tool_is_noop(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "inject_env_vars.yaml").write_text("vars:\n  FOO: bar\n", encoding="utf-8")
    result = _run_hook(project, "Read", "n/a")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_e2e_injects_literal_and_at_reference_bash(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "secrets").mkdir()
    (config_dir / "secrets" / "local.env").write_text("FROM_FILE=secret-value\n", encoding="utf-8")
    (config_dir / "inject_env_vars.yaml").write_text(
        'override: false\nvars:\n  LITERAL_VAR: hello-world\n  FROM_FILE: "@secrets/local.env"\n',
        encoding="utf-8",
    )

    result = _run_hook(project, "Bash", "echo test")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    command = output["hookSpecificOutput"]["updatedInput"]["command"]
    assert "export LITERAL_VAR='hello-world'" in command
    assert "export FROM_FILE='secret-value'" in command
    assert command.endswith("echo test")
    assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
    # Notification of injected keys is on by default.
    assert "LITERAL_VAR" in output["systemMessage"]
    assert "FROM_FILE" in output["systemMessage"]


def test_e2e_notify_disabled_via_dotenv_suppresses_message(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "inject_env_vars.yaml").write_text(
        "vars:\n  LITERAL_VAR: hello-world\n", encoding="utf-8"
    )

    result = _run_hook(project, "Bash", "echo test", extra_env={"NOTIFY_INJECTED_VARS": "false"})
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert (
        "export LITERAL_VAR='hello-world'"
        in output["hookSpecificOutput"]["updatedInput"]["command"]
    )
    assert "systemMessage" not in output


def test_e2e_default_override_false_skips_existing_env_var(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "inject_env_vars.yaml").write_text(
        "override: false\nvars:\n  ALREADY_SET: new-value\n", encoding="utf-8"
    )

    result = _run_hook(project, "Bash", "echo test", extra_env={"ALREADY_SET": "old-value"})
    assert result.returncode == 0
    # Nothing left to inject -> no updatedInput, command is untouched by the hook.
    assert result.stdout.strip() == ""


def test_e2e_override_true_overwrites_existing_env_var(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "inject_env_vars.yaml").write_text(
        "override: true\nvars:\n  ALREADY_SET: new-value\n", encoding="utf-8"
    )

    result = _run_hook(project, "Bash", "echo test", extra_env={"ALREADY_SET": "old-value"})
    assert result.returncode == 0
    output = json.loads(result.stdout)
    command = output["hookSpecificOutput"]["updatedInput"]["command"]
    assert "export ALREADY_SET='new-value'" in command


def test_e2e_missing_reference_warns_but_does_not_block(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "inject_env_vars.yaml").write_text(
        'vars:\n  LITERAL_VAR: kept\n  MISSING: "@secrets/nope.env"\n',
        encoding="utf-8",
    )

    result = _run_hook(project, "Bash", "echo test")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    command = output["hookSpecificOutput"]["updatedInput"]["command"]
    assert "export LITERAL_VAR='kept'" in command
    assert "MISSING" not in command
    assert "MISSING" in output["systemMessage"]


def test_e2e_powershell_uses_env_syntax(tmp_path):
    project, config_dir = _make_project(tmp_path)
    (config_dir / "inject_env_vars.yaml").write_text("vars:\n  FOO: bar\n", encoding="utf-8")

    result = _run_hook(project, "PowerShell", "Get-ChildItem")
    assert result.returncode == 0
    output = json.loads(result.stdout)
    command = output["hookSpecificOutput"]["updatedInput"]["command"]
    assert command == "$env:FOO='bar'\nGet-ChildItem"


if __name__ == "__main__":
    raise SystemExit(
        subprocess.run([sys.executable, "-m", "pytest", str(Path(__file__)), "-v"]).returncode
    )
