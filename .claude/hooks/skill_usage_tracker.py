#!/usr/bin/env python3
"""<hooks>
description: Skillツール呼び出し、またはSKILL.mdの直接Readを検知し、対象スキルのfrontmatterにauto-enquete:trueがある場合のみセッション内スキル使用状況を記録するフックの設定
event: PostToolUse
matcher: "^(Skill|Read)$"
hook:
  type: command
  command: python
  args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/skill_usage_tracker.py"]
</hooks>

PostToolUse hook for the Skill tool and the Read tool.

Detects "a skill was used" broadly: either the Skill tool was invoked, or a
SKILL.md file was Read directly (e.g. because recommend_skills.py's
additionalContext points at a SKILL.md path for a skill not registered with
the Skill tool in this session, and tells Claude to Read it instead).

Only records usage for skills whose SKILL.md frontmatter has
`auto-enquete: true` (default false) -- a deliberate opt-in so most skills
are never tracked or surveyed. When a match is found, the skill's name and
directory are appended to a per-session state file at
`.claude/hooks/state/skill_usage/<session_id>.json`. The companion Stop
hook (`skill_enquete_stop.py`) reads that file to ask Claude for usability
feedback once the turn ends.

Never blocks the tool call: any resolution failure (skill name not
resolvable to a path, missing/invalid frontmatter, no session_id, ...) just
skips recording silently.
"""

"""
環境変数（省略可）:
- `HOOK_LOG` このフックの「デバッグログ」を`.claude/hooks/logs/skill_usage_tracker/`に
             書き出すかどうか（true/false等）。フック自体の有効/無効ではない
             （そちらは`.claude/scripts/hooks.yml`の`enabled`で管理する）。
             未設定ならスクリプト先頭の`ENABLE_HOOK_LOG`に従う。
             `.claude/hooks/.env`に設定されていればそちらが優先。
"""
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import runtime
from _lib import skill_enquete_state as state_mod
from _lib import skill_frontmatter as fm

# Debug-log ON/OFF only (writes to .claude/hooks/logs/skill_usage_tracker/) --
# NOT whether this hook itself runs (that's .claude/scripts/hooks.yml's `enabled`).
# `.claude/hooks/.env`'s HOOK_LOG, if set, overrides this default.
ENABLE_HOOK_LOG = False

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
CONFIG_RELATIVE = Path(".claude") / "hooks" / "config" / f"{SCRIPT_NAME}.yaml"
DEFAULT_ROOTS = ()


def load_roots(project_dir):
    """Repo-relative roots from config/skill_usage_tracker.yaml, plus the
    user-scoped `~/.claude/skills` dir (always included, not configurable
    here since it lives outside the repo). Config-file roots only ever add
    to this, never replace it."""
    config_path = project_dir / CONFIG_RELATIVE
    raw_roots = list(DEFAULT_ROOTS)
    if config_path.is_file():
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            data = None
        configured = (data or {}).get("roots") if isinstance(data, dict) else None
        if isinstance(configured, list):
            raw_roots += [r for r in configured if isinstance(r, str) and r.strip()]

    seen = set()
    roots = []
    for r in raw_roots:
        if r not in seen:
            seen.add(r)
            roots.append(project_dir / r)
    roots.append(Path.home() / ".claude" / "skills")
    return roots


def resolve_skill_md_for_read(file_path):
    path = Path(file_path)
    if path.name != "SKILL.md":
        return None
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    if not resolved.is_file():
        return None
    return resolved


def main():
    payload, log, finish = runtime.init_hook_context(SCRIPT_NAME, ENABLE_HOOK_LOG)

    tool_name = payload.get("tool_name")
    log["tool_name"] = tool_name
    if tool_name not in ("Skill", "Read"):
        finish(0, reason="not a Skill/Read call")

    session_id = payload.get("session_id")
    if not session_id:
        finish(0, reason="no session_id in payload")

    tool_input = payload.get("tool_input") or {}
    project_dir = state_mod.resolve_project_dir()

    if tool_name == "Read":
        file_path = tool_input.get("file_path")
        if not file_path:
            finish(0, reason="no file_path in tool_input")
        skill_md_path = resolve_skill_md_for_read(file_path)
        if skill_md_path is None:
            finish(0, reason="not a SKILL.md read")
    else:  # Skill
        skill_arg = tool_input.get("skill")
        if not isinstance(skill_arg, str) or not skill_arg.strip():
            finish(0, reason="no skill name in tool_input")
        # "plugin:skill" form -> match on the bare skill name.
        bare_name = skill_arg.strip().split(":")[-1].strip()
        roots = load_roots(project_dir)
        skill_dir = fm.find_skill_dir_by_name(bare_name, roots)
        if skill_dir is None:
            finish(0, reason="skill name not resolved to a path", skill=skill_arg)
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.is_file():
            finish(0, reason="resolved dir has no SKILL.md", skill=skill_arg)

    frontmatter = fm.read_frontmatter(skill_md_path)
    if frontmatter is None:
        finish(0, reason="no/invalid frontmatter", path=str(skill_md_path))

    if frontmatter.get("auto-enquete") is not True:
        finish(0, reason="auto-enquete not enabled", path=str(skill_md_path))

    skill_name = frontmatter.get("name")
    if not isinstance(skill_name, str) or not skill_name.strip():
        skill_name = skill_md_path.parent.name
    skill_name = skill_name.strip()

    state_file = state_mod.state_path(project_dir, session_id)
    data = state_mod.load_state(state_file)
    is_new = skill_name not in data["skills"]
    data["skills"][skill_name] = {"dir": skill_md_path.parent.resolve().as_posix()}
    state_mod.save_state(state_file, data)

    finish(0, reason="recorded" if is_new else "already recorded", skill=skill_name)


if __name__ == "__main__":
    main()
