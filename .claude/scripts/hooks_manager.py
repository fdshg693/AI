#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Manage Claude Code hooks via a contract embedded in each hook script.

Each `.claude/hooks/*.py` script that wants to be picked up here declares a
`<hooks>...</hooks>` YAML block inside its own module docstring (the file's
first triple-quoted string). A docstring may contain more than one such
block -- one script registering itself for several events (e.g. one script
handling both `PostToolUse` and `PostToolUseFailure`) -- in which case each
block becomes its own `hooks.yml` entry, keyed `"<file>#<event>"` instead of
the plain filename. Two subcommands operate on the resulting contracts:

  sync    - scan .claude/hooks/*.py, upsert descriptions/format into hooks.yml
            (never touches the `enabled` flag of an existing entry)
  reflect - write the settings.json "hooks" key from the entries in
            hooks.yml that have `enabled: true`

hooks.yml is treated as a generated file: entries whose backing script no
longer exists are dropped automatically. Toggle a hook on/off by editing its
`enabled` field in hooks.yml, then run `reflect`.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CLAUDE_DIR = SCRIPT_DIR.parent
HOOKS_DIR = CLAUDE_DIR / "hooks"
# Standalone test/verification scripts live here and are never hook scripts:
# discover_contracts() skips them so a stray <hooks> block in a test can't
# leak into hooks.yml / settings.json.
TESTS_DIR = HOOKS_DIR / "tests"
HOOKS_YAML_PATH = SCRIPT_DIR / "hooks.yml"
SETTINGS_JSON_PATH = CLAUDE_DIR / "settings.json"

HOOKS_TAG_RE = re.compile(r"<hooks>(.*?)</hooks>", re.DOTALL)

VALID_EVENTS = {
    "SessionStart",
    "Setup",
    "UserPromptSubmit",
    "UserPromptExpansion",
    "PreToolUse",
    "PermissionRequest",
    "PermissionDenied",
    "PostToolUse",
    "PostToolUseFailure",
    "PostToolBatch",
    "Notification",
    "MessageDisplay",
    "SubagentStart",
    "SubagentStop",
    "TaskCreated",
    "TaskCompleted",
    "Stop",
    "StopFailure",
    "TeammateIdle",
    "InstructionsLoaded",
    "ConfigChange",
    "CwdChanged",
    "FileChanged",
    "WorktreeCreate",
    "WorktreeRemove",
    "PreCompact",
    "PostCompact",
    "Elicitation",
    "ElicitationResult",
    "SessionEnd",
}

NO_MATCHER_EVENTS = {
    "UserPromptSubmit",
    "PostToolBatch",
    "Stop",
    "TeammateIdle",
    "TaskCreated",
    "TaskCompleted",
    "WorktreeCreate",
    "WorktreeRemove",
    "MessageDisplay",
    "CwdChanged",
}

VALID_HOOK_TYPES = {"command", "http", "mcp_tool", "prompt", "agent"}
REQUIRED_HOOK_FIELDS = {
    "command": ("command",),
    "http": ("url",),
    "mcp_tool": ("server", "tool"),
}


class ContractError(Exception):
    """A hook contract (or hooks.yml) fails validation."""


@dataclass
class HookContract:
    script_name: str
    description: str
    event: str
    matcher: str | None
    hook: dict[str, Any]


def _validate_contract(script_name: str, data: dict[str, Any]) -> HookContract:
    missing = [key for key in ("description", "event", "hook") if key not in data]
    if missing:
        raise ContractError(
            f"{script_name}: <hooks>ブロックに必須キーがありません: {', '.join(missing)}"
        )

    description = data["description"]
    if not isinstance(description, str) or not description.strip():
        raise ContractError(f"{script_name}: descriptionは空でない文字列である必要があります")

    event = data["event"]
    if event not in VALID_EVENTS:
        raise ContractError(f"{script_name}: 未知のevent '{event}' です")

    matcher = data.get("matcher")
    if matcher is not None and not isinstance(matcher, str):
        raise ContractError(f"{script_name}: matcherは文字列またはnullである必要があります")
    if matcher is not None and event in NO_MATCHER_EVENTS:
        raise ContractError(
            f"{script_name}: event '{event}' はmatcher非対応です。matcherを削除してください"
        )

    hook = data["hook"]
    if not isinstance(hook, dict):
        raise ContractError(f"{script_name}: hookフィールドはマッピングである必要があります")
    hook_type = hook.get("type")
    if hook_type not in VALID_HOOK_TYPES:
        raise ContractError(f"{script_name}: hook.typeが不正です: {hook_type!r}")
    for field in REQUIRED_HOOK_FIELDS.get(hook_type, ()):
        if field not in hook:
            raise ContractError(
                f"{script_name}: hook.type={hook_type}の場合、hook.{field}が必須です"
            )

    return HookContract(
        script_name=script_name,
        description=description.strip(),
        event=event,
        matcher=matcher,
        hook=hook,
    )


def extract_contract(path: Path) -> list[HookContract]:
    """Return the hook contracts declared in path's module docstring (empty
    list if the file declares no `<hooks>` block at all, e.g. a shared
    helper). A docstring may contain more than one `<hooks>...</hooks>` tag
    -- one script registering itself for several events (e.g. `PostToolUse`
    +`PostToolUseFailure`) -- in which case each contract's `script_name` is
    disambiguated to `"<file>#<event>"` so both get their own entry in
    `hooks.yml`. A single block keeps the plain filename as before, so
    existing single-contract scripts are unaffected."""
    source = path.read_text(encoding="utf-8")
    try:
        module = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise ContractError(f"{path.name}: 構文エラーのため読み込めません: {exc}") from exc

    docstring = ast.get_docstring(module, clean=False)
    if docstring is None:
        return []
    matches = list(HOOKS_TAG_RE.finditer(docstring))
    if not matches:
        return []

    contracts = []
    for match in matches:
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise ContractError(f"{path.name}: <hooks>ブロックのYAMLが不正です: {exc}") from exc
        if not isinstance(data, dict):
            raise ContractError(f"{path.name}: <hooks>ブロックはマッピングである必要があります")
        contracts.append(_validate_contract(path.name, data))

    if len(contracts) > 1:
        seen: set[str] = set()
        for contract in contracts:
            key = f"{path.name}#{contract.event}"
            if key in seen:
                raise ContractError(
                    f"{path.name}: 同じevent '{contract.event}' の<hooks>ブロックが複数あります。"
                    "1ブロックにまとめるかeventを分けてください"
                )
            seen.add(key)
            contract.script_name = key

    return contracts


def _is_excluded(path: Path) -> bool:
    """True for paths under the `tests/` subdirectory (or any other non-hook
    script location). Such files are verification scripts, not hooks, and must
    never be picked up even if they happened to declare a <hooks> block."""
    try:
        path.relative_to(TESTS_DIR)
    except ValueError:
        return False
    return True


def discover_contracts() -> list[HookContract]:
    contracts = []
    errors = []
    for path in sorted(HOOKS_DIR.glob("*.py")):
        if _is_excluded(path):
            continue
        try:
            contracts.extend(extract_contract(path))
        except ContractError as exc:
            errors.append(str(exc))
            continue
    if errors:
        raise ContractError("\n".join(errors))
    return contracts


def load_hooks_yaml() -> dict[str, Any]:
    if not HOOKS_YAML_PATH.exists():
        return {}
    data = yaml.safe_load(HOOKS_YAML_PATH.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ContractError(
            f"{HOOKS_YAML_PATH.name}の形式が不正です（マッピングである必要があります）"
        )
    return data


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    # No trailing newline, LF only: matches this repo's existing settings.json
    # byte-for-byte (repo-wide .gitattributes normalizes text to eol=lf, and
    # the file predates any trailing newline convention).
    text = json.dumps(data, indent=2, ensure_ascii=False)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def _contract_entry(contract: HookContract, enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "description": contract.description,
        "event": contract.event,
        "matcher": contract.matcher,
        "hook": contract.hook,
    }


def _entry_content_changed(prev: dict[str, Any], new: dict[str, Any]) -> bool:
    fields = ("description", "event", "matcher", "hook")
    return any(prev.get(field) != new.get(field) for field in fields)


def cmd_sync() -> int:
    try:
        contracts = discover_contracts()
        existing = load_hooks_yaml()
    except ContractError as exc:
        print(f"sync失敗:\n{exc}", file=sys.stderr)
        return 1

    known_names = {c.script_name for c in contracts}
    removed = sorted(name for name in existing if name not in known_names)

    new_data: dict[str, Any] = {}
    added: list[str] = []
    updated: list[str] = []
    for contract in contracts:
        prev = existing.get(contract.script_name)
        enabled = bool(prev.get("enabled", False)) if isinstance(prev, dict) else False
        entry = _contract_entry(contract, enabled)
        new_data[contract.script_name] = entry
        if prev is None:
            added.append(contract.script_name)
        elif _entry_content_changed(prev, entry):
            updated.append(contract.script_name)

    if new_data == existing:
        print("変更なし。hooks.ymlは最新です。")
        return 0

    _write_yaml(HOOKS_YAML_PATH, new_data)

    for name in added:
        print(f"追加: {name} (enabled: false)")
    for name in updated:
        print(f"更新: {name}")
    for name in removed:
        print(f"削除: {name}（対応するスクリプトが見つかりません）")
    return 0


def _validated_enabled_entry(name: str, entry: Any) -> HookContract:
    if not isinstance(entry, dict):
        raise ContractError(f"{name}: hooks.ymlのエントリはマッピングである必要があります")
    return _validate_contract(name, entry)


def cmd_reflect() -> int:
    try:
        hooks_data = load_hooks_yaml()
    except ContractError as exc:
        print(f"reflect失敗: {exc}", file=sys.stderr)
        return 1

    enabled_contracts: list[HookContract] = []
    try:
        for name, entry in sorted(hooks_data.items()):
            if isinstance(entry, dict) and entry.get("enabled"):
                enabled_contracts.append(_validated_enabled_entry(name, entry))
    except ContractError as exc:
        print(f"reflect失敗: {exc}", file=sys.stderr)
        return 1

    hooks_section: dict[str, list[dict[str, Any]]] = {}
    for contract in enabled_contracts:
        groups = hooks_section.setdefault(contract.event, [])
        group = next((g for g in groups if g.get("matcher") == contract.matcher), None)
        if group is None:
            group = {"hooks": []}
            if contract.matcher is not None:
                group["matcher"] = contract.matcher
            groups.append(group)
        group["hooks"].append(contract.hook)

    if not SETTINGS_JSON_PATH.exists():
        settings: dict[str, Any] = {}
    else:
        try:
            settings = json.loads(SETTINGS_JSON_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(
                f"reflect失敗: {SETTINGS_JSON_PATH.name}のパースに失敗しました: {exc}",
                file=sys.stderr,
            )
            return 1
        if not isinstance(settings, dict):
            print(
                f"reflect失敗: {SETTINGS_JSON_PATH.name}の形式が不正です（オブジェクトである必要があります）",
                file=sys.stderr,
            )
            return 1

    before = settings.get("hooks")
    if hooks_section:
        settings["hooks"] = hooks_section
    else:
        settings.pop("hooks", None)

    if settings.get("hooks") == before:
        print("変更なし。settings.jsonは最新です。")
        return 0

    _write_json(SETTINGS_JSON_PATH, settings)
    names = [c.script_name for c in enabled_contracts]
    print(f"反映済み: {', '.join(names) if names else '（有効なフックなし）'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("sync", help=".claude/hooks/*.py の契約を hooks.yml に反映する")
    subparsers.add_parser("reflect", help="hooks.yml の有効なフックを settings.json に反映する")

    args = parser.parse_args(argv)
    if args.command == "sync":
        return cmd_sync()
    return cmd_reflect()


if __name__ == "__main__":
    sys.exit(main())
