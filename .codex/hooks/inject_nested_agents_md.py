#!/usr/bin/env python3
"""PreToolUse hook: inject AGENTS.md files that Codex's own session-start
discovery does NOT cover.

Codex builds its instruction chain once per session by walking from the
project root down to the *initial* cwd only (see
codex-plugins/meta/skills/codex-memory/SKILL.md section 2). Files read or
edited outside that root->cwd path never get their local AGENTS.md
pulled in automatically -- unlike Claude Code's CLAUDE.md, which loads a
subdirectory's CLAUDE.md the moment Claude reads any file under it (see
claude-plugins/meta/skills/claude-code-memory/memory.md line 31), Codex
has no dedicated "Read" tool: apply_patch is the only structured
file-editing tool, and file reads normally go through arbitrary shell
commands (Bash / exec_command). This hook fires on apply_patch and Bash
calls, tries to work out which files/directories are actually being
touched (structured parsing for apply_patch, a best-effort heuristic
over common read commands for Bash), finds the AGENTS.override.md /
AGENTS.md files for their ancestor directories, skips whatever the
root->cwd walk already covered, and feeds the rest back in as
additionalContext.

The Bash-side detection is inherently a heuristic (arbitrary shell
commands can read files in ways this script won't recognize) and is not
a substitute for the deterministic apply_patch coverage.

Never blocks: on any error, it exits 0 with no output so the tool call
is unaffected.
"""

import json
import os
import re
import sys
import tempfile

CANDIDATE_NAMES = ("AGENTS.override.md", "AGENTS.md")
MAX_CONTEXT_BYTES = 16_000
PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$")

# Best-effort table of common file-reading commands (Git Bash / POSIX and
# PowerShell/cmd, since this repo runs on Windows with both shells
# available). `flag_values`: flags that consume the next token as their
# value (so it must not be treated as a path). `skip_first_positional`:
# the command's first non-flag argument is a pattern/script, not a path
# (grep/rg/findstr/Select-String's search pattern, sed's script when no
# -e/-f was given).
BASH_READ_COMMAND_SPECS = {
    "cat": {"flag_values": set()},
    "less": {"flag_values": set()},
    "more": {"flag_values": set()},
    "type": {"flag_values": set()},
    "head": {"flag_values": {"-n", "-c"}},
    "tail": {"flag_values": {"-n", "-c"}},
    "sed": {
        "flag_values": {"-e", "-f", "-i"},
        "skip_first_positional": True,
        "unless_flags": {"-e", "-f"},
    },
    "get-content": {
        "flag_values": {"-totalcount", "-tail", "-readcount", "-delimiter", "-encoding", "-stream"},
    },
    "gc": {
        "flag_values": {"-totalcount", "-tail", "-readcount", "-delimiter", "-encoding", "-stream"},
    },
    "grep": {
        "flag_values": {"-e", "-f", "-m", "-a", "-b", "-c", "-g", "-t"},
        "skip_first_positional": True,
    },
    "rg": {
        "flag_values": {
            "-e",
            "-f",
            "-m",
            "-a",
            "-b",
            "-c",
            "-g",
            "-t",
            "--type",
            "--glob",
            "--context",
        },
        "skip_first_positional": True,
    },
    "findstr": {"flag_values": set(), "skip_first_positional": True},
    "select-string": {
        "flag_values": {"-pattern", "-context", "-encoding"},
        "skip_first_positional": True,
    },
}
CD_COMMANDS = {"cd", "chdir", "pushd", "set-location", "sl"}
TOKEN_RE = re.compile(r"""'[^']*'|"[^"]*"|\S+""")


def find_repo_root(start_dir):
    current = os.path.abspath(start_dir)
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(start_dir)
        current = parent


def ancestor_chain(root, target_dir):
    """Directories from root down to target_dir, inclusive. [] if target_dir
    is not inside root."""
    root = os.path.normcase(os.path.normpath(root))
    target_dir = os.path.normpath(target_dir)
    target_norm = os.path.normcase(target_dir)
    if target_norm != root and not target_norm.startswith(root + os.sep):
        return []

    chain = []
    current = target_dir
    while True:
        chain.append(current)
        if os.path.normcase(os.path.normpath(current)) == root:
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    chain.reverse()
    return chain


def strip_quotes(token):
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    return token


def tokenize(s):
    return [strip_quotes(t) for t in TOKEN_RE.findall(s)]


def split_subcommands(command):
    """Split a shell command string on unquoted ; & | and newlines."""
    parts = []
    current = []
    quote = None
    for ch in command:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            current.append(ch)
            continue
        if ch in (";", "&", "|", "\n"):
            parts.append("".join(current))
            current = []
            continue
        current.append(ch)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def extract_bash_dirs(command, cwd):
    """Best-effort: guess which files/dirs a shell command reads, by
    recognizing common read commands (cat/head/tail/sed/rg/grep/... and
    their PowerShell equivalents). Only paths that actually exist on disk
    are kept, which filters out most mis-parsed patterns/flags.

    Tracks a virtual cwd across `cd`/`Set-Location` in a chained command
    (e.g. `cd tools/foo && cat AGENTS.md`) so later subcommands in the
    same chain resolve relative paths correctly."""
    dirs = set()
    virtual_cwd = cwd
    for subcmd in split_subcommands(command):
        tokens = tokenize(subcmd)
        if not tokens:
            continue
        name = re.sub(r"\.(exe|ps1)$", "", os.path.basename(tokens[0]).lower())

        if name in CD_COMMANDS:
            target = next((t for t in tokens[1:] if not t.startswith("-")), None)
            if target:
                virtual_cwd = os.path.normpath(
                    target if os.path.isabs(target) else os.path.join(virtual_cwd, target)
                )
            continue

        spec = BASH_READ_COMMAND_SPECS.get(name)
        if spec is None:
            continue

        flag_values = spec.get("flag_values", set())
        flags_present = {t.lower() for t in tokens[1:] if t.startswith("-")}
        skip_first = spec.get("skip_first_positional", False)
        unless_flags = spec.get("unless_flags")
        if unless_flags and flags_present & unless_flags:
            skip_first = False

        positionals = []
        i = 1
        while i < len(tokens):
            t = tokens[i]
            if t.startswith("-"):
                i += 2 if t.lower() in flag_values else 1
                continue
            positionals.append(t)
            i += 1
        if skip_first and positionals:
            positionals = positionals[1:]

        for p in positionals:
            if not p or p in ("-", ".", ".."):
                continue
            abs_path = os.path.normpath(p if os.path.isabs(p) else os.path.join(virtual_cwd, p))
            if os.path.isdir(abs_path):
                dirs.add(abs_path)
            elif os.path.isfile(abs_path):
                dirs.add(os.path.dirname(abs_path))
    return dirs


def extract_touched_dirs(tool_name, tool_input, cwd):
    dirs = set()

    if tool_name == "apply_patch":
        command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
        for line in command.splitlines():
            m = PATCH_FILE_RE.match(line.strip())
            if not m:
                continue
            raw_path = m.group(1).strip()
            abs_path = raw_path if os.path.isabs(raw_path) else os.path.join(cwd, raw_path)
            dirs.add(os.path.dirname(os.path.normpath(abs_path)))
        return dirs

    if tool_name == "Bash":
        command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
        return extract_bash_dirs(command, cwd)

    # Generic fallback for other file-oriented tools (MCP fs tools etc.)
    if isinstance(tool_input, dict):
        for key in ("file_path", "path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                abs_path = value if os.path.isabs(value) else os.path.join(cwd, value)
                dirs.add(os.path.dirname(os.path.normpath(abs_path)))

    return dirs


def load_cache(session_id):
    cache_path = os.path.join(tempfile.gettempdir(), "codex-nested-agents-md", f"{session_id}.json")
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return cache_path, set(json.load(f))
    except Exception:
        return cache_path, set()


def save_cache(cache_path, seen):
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(sorted(seen), f)
    except Exception:
        pass


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    cwd = event.get("cwd") or os.getcwd()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    session_id = event.get("session_id", "unknown")

    touched_dirs = extract_touched_dirs(tool_name, tool_input, cwd)
    if not touched_dirs:
        return 0

    root = find_repo_root(cwd)
    covered = set(os.path.normcase(os.path.normpath(d)) for d in ancestor_chain(root, cwd))

    cache_path, seen = load_cache(session_id)

    found = []  # (relative_label, content)
    newly_seen = set()
    for touched_dir in touched_dirs:
        for d in ancestor_chain(root, touched_dir):
            norm_d = os.path.normcase(os.path.normpath(d))
            if norm_d in covered or norm_d in seen or norm_d in newly_seen:
                continue
            newly_seen.add(norm_d)
            for name in CANDIDATE_NAMES:
                candidate = os.path.join(d, name)
                if not os.path.isfile(candidate):
                    continue
                try:
                    with open(candidate, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().strip()
                except Exception:
                    content = ""
                if content:
                    rel = os.path.relpath(candidate, root).replace(os.sep, "/")
                    found.append((rel, content))
                break  # override takes precedence over AGENTS.md, one file per dir

    save_cache(cache_path, seen | newly_seen)

    if not found:
        return 0

    parts = []
    total = 0
    for rel, content in found:
        block = f"{rel}:\n{content}\n"
        if total + len(block) > MAX_CONTEXT_BYTES:
            parts.append(
                f"(truncated: remaining AGENTS.md files omitted, over {MAX_CONTEXT_BYTES} bytes)"
            )
            break
        parts.append(block)
        total += len(block)

    additional_context = (
        "The following AGENTS.md files apply to files you are about to read "
        "or edit but were outside the project-root -> initial-cwd path Codex "
        "loads automatically at session start:\n\n" + "\n".join(parts)
    )

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": additional_context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
