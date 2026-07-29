"""List the name + description of every sibling SKILL.md under repo-meta/skills/.

Used as this skill's dynamic context injection (`` !`python .../list_sibling_skills.py` ``
in SKILL.md) so the routing list is always read live from the actual sibling
SKILL.md files instead of a hand-maintained copy that can drift out of sync
when a repo-meta skill is added, renamed, or has its description edited.

Only a minimal top-level-key frontmatter scan is done here (no PyYAML
dependency, so this script runs with the plain `python` on PATH and does not
need `uv run`). This is safe for this repo's repo-meta/skills/*/SKILL.md
files today because their `name`/`description` are single-line scalars; it
would need to grow a real YAML parser if that ever changes.
"""

from __future__ import annotations

import re
from pathlib import Path

TOP_LEVEL_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return top-level scalar frontmatter fields, or None if there is no frontmatter block."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    for line in text[3:end].splitlines():
        # Skip blank lines, `#` comments, and indented lines (nested keys like meta:'s
        # subfields) — only top-level scalars (name/description) are wanted here.
        if not line or line[0] in (" ", "\t", "#"):
            continue
        match = TOP_LEVEL_FIELD_RE.match(line)
        if match:
            fields[match.group(1)] = strip_yaml_quotes(match.group(2).strip())
    return fields


def strip_yaml_quotes(value: str) -> str:
    """Strip one layer of matching '...'/"..." quoting, as a real YAML parser would."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def main() -> int:
    self_skill_dir = Path(__file__).resolve().parent.parent
    skills_root = self_skill_dir.parent

    entries: list[tuple[str, str]] = []
    errors: list[str] = []
    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        if skill_dir == self_skill_dir:
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{skill_md.as_posix()}: 読み込み失敗 ({exc})")
            continue
        fields = parse_frontmatter(text)
        if fields is None:
            errors.append(f"{skill_md.as_posix()}: frontmatterの解析に失敗しました")
            continue
        name = fields.get("name", skill_dir.name)
        description = fields.get("description", "(descriptionが未設定)")
        entries.append((name, description))

    entries.sort(key=lambda entry: entry[0])

    if not entries:
        print("(repo-meta/skills配下に他のSKILL.mdが見つかりませんでした)")
    for name, description in entries:
        print(f"- **{name}**: {description}")

    for error in errors:
        print(f"- [ERROR] {error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
