#!/usr/bin/env python3
"""Shared debug-logging helper for hook scripts in this directory.

This module controls only whether a hook writes a debug log of its own
invocation -- it is unrelated to whether the hook itself runs at all (that
is decided entirely by `.claude/scripts/hooks.yml`, reflected into
`.claude/settings.json`).

Each hook script defines its own top-level `ENABLE_HOOK_LOG` boolean to
switch its debug log on/off. If `.claude/hooks/.env` (or the process
environment) defines `HOOK_LOG`, that value wins over the script's default.

`resolve_bool_flag()` is the same true/false-from-`.env` resolution, but for
any key -- other hook scripts use it for their own `.env`-managed toggles
(e.g. `inject_env_vars.py`'s `NOTIFY_INJECTED_VARS`).

When the debug log is on, `write_log()` writes one JSON file per hook
invocation to `.claude/hooks/logs/{script_name}/{time-sortable id}.log`, so
individual runs never overwrite each other and `ls` sorts them chronologically.

This module must never raise -- a logging failure must never be the reason
a hook blocks or breaks the tool call it's attached to.
"""

import datetime
import json
import os
import time
import uuid
from pathlib import Path

from .dotenv import load_dotenv_value

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", "")
DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
LOGS_ROOT = os.path.join(PROJECT_DIR, ".claude", "hooks", "logs")

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def resolve_bool_flag(key, default):
    """Resolve a boolean on/off flag shared across hook scripts.

    `key` from the environment or `.claude/hooks/.env` overrides `default`
    when set to a recognized true/false value. Unrecognized or unset values
    fall back to `default`. Used for per-script toggles like `HOOK_LOG`
    (debug logging) or `NOTIFY_INJECTED_VARS` (inject_env_vars.py's
    injected-vars notification).
    """
    raw = os.environ.get(key)
    if raw is None:
        raw = load_dotenv_value(DOTENV_PATH, key)
    if raw is None:
        return default

    normalized = raw.strip().lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    return default


def is_log_enabled(default):
    """Resolve the effective DEBUG-LOG on/off state for this invocation.

    This governs debug logging only, not whether the hook itself is active
    (that's `.claude/scripts/hooks.yml`'s `enabled` field).
    """
    return resolve_bool_flag("HOOK_LOG", default)


def _uuid7_hex():
    """Time-ordered UUID (RFC 9562 UUIDv7) so log filenames sort chronologically.

    Backfills `uuid.uuid7()` (stdlib only from Python 3.14) since only the
    time-ordering property of v7 is needed here.
    """
    ts_ms = int(time.time() * 1000)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0xFFF
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    value = (ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return str(uuid.UUID(int=value))


def write_log(script_name, record):
    """Best-effort write of `record` to its own file under logs/{script_name}/."""
    try:
        script_dir = os.path.join(LOGS_ROOT, script_name)
        os.makedirs(script_dir, exist_ok=True)
        log_path = os.path.join(script_dir, f"{_uuid7_hex()}.log")

        record = dict(record)
        record.setdefault("timestamp", datetime.datetime.now().astimezone().isoformat())

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass
