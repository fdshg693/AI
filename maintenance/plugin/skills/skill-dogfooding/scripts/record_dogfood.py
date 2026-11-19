"""Write one entry of the dogfooding ledger (maintenance/skill-risk/dogfood.yaml).

Replaces the entry for the given canonical ID (the ledger keeps only the latest
run per skill; history is in git) and rewrites the ``entries:`` block in sorted
key order. The header comments above ``entries:`` are kept as they are.

Validates what rank_skill_risk.py relies on: the SKILL.md exists, verdict is
ok | needs-fix | fixed, date is YYYY-MM-DD, fix is "<repo>@<short-hash>".

Usage (from the repository root):
  uv run python maintenance/plugin/skills/skill-dogfooding/scripts/record_dogfood.py \
      <canonical-id> --verdict needs-fix --fb 20261120-100000-fb.md
  ... <canonical-id> --verdict fixed --fix skills@abc1234
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml

LEDGER = Path("maintenance/skill-risk/dogfood.yaml")
VERDICTS = ("ok", "needs-fix", "fixed")
FIELD_ORDER = ("date", "verdict", "fb", "note", "fix")
FIX_RE = re.compile(r"^[A-Za-z0-9._/-]+@[0-9a-f]{7,40}$")
FB_RE = re.compile(r"^\d{8}-\d{6}(-\d+)?-fb\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def find_root(start: Path) -> Path:
    for p in (start, *start.parents):
        if (p / ".umbrella-root").exists():
            return p
    raise SystemExit("error: run inside the umbrella repository (no .umbrella-root found)")


def render_entries(entries: dict[str, dict[str, str]]) -> str:
    if not entries:
        return "entries: {}\n"
    out = ["entries:"]
    for key in sorted(entries):
        out.append(f"  {key}:")
        entry = entries[key]
        for field in FIELD_ORDER:
            if field in entry and entry[field] not in (None, ""):
                if field == "date":  # plain YAML date, validated as YYYY-MM-DD
                    out.append(f"    date: {entry[field]}")
                    continue
                value = yaml.safe_dump(str(entry[field]), allow_unicode=True, width=10_000).strip()
                value = value.removesuffix("\n...").removesuffix("...").strip()
                out.append(f"    {field}: {value}")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="record_dogfood", description=__doc__.split("\n\n")[0])
    p.add_argument("skill", help="canonical ID: umbrella-relative .../SKILL.md path")
    p.add_argument("--verdict", required=True, choices=VERDICTS)
    p.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD (default: today)")
    p.add_argument("--fb", help="fb file name under tools/skill-tools/fb/skills/<name>/")
    p.add_argument("--note", help="one-line summary (for skills --fb cannot resolve)")
    p.add_argument("--fix", help='improving commit as "<repo>@<short-hash>" (with --verdict fixed)')
    p.add_argument(
        "--keep", action="store_true", help="keep fb/note from the existing entry when not given"
    )
    args = p.parse_args(argv)

    root = find_root(Path.cwd().resolve())
    skill = args.skill.replace("\\", "/").removeprefix("./")
    if not skill.endswith("/SKILL.md") or not (root / skill).is_file():
        print(f"error: not an existing umbrella-relative SKILL.md path: {skill}", file=sys.stderr)
        return 2
    if not DATE_RE.match(args.date):
        print(f"error: --date must be YYYY-MM-DD: {args.date}", file=sys.stderr)
        return 2
    if args.fb and not FB_RE.match(args.fb):
        print(
            f"error: --fb must be a file name like 20261120-100000-fb.md: {args.fb}",
            file=sys.stderr,
        )
        return 2
    if args.fix and not FIX_RE.match(args.fix):
        print(f'error: --fix must be "<repo>@<short-hash>": {args.fix}', file=sys.stderr)
        return 2
    if args.fix and args.verdict != "fixed":
        print("error: --fix is only valid with --verdict fixed", file=sys.stderr)
        return 2
    if args.note and "\n" in args.note:
        print("error: --note must be one line", file=sys.stderr)
        return 2

    path = root / LEDGER
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^entries:", text, flags=re.MULTILINE)
    if not match:
        print(f"error: no top-level 'entries:' in {LEDGER}", file=sys.stderr)
        return 2
    header = text[: match.start()]
    data = yaml.safe_load(text) or {}
    entries = {k: dict(v or {}) for k, v in (data.get("entries") or {}).items()}

    old = entries.get(skill, {})
    new: dict[str, str] = {"date": args.date, "verdict": args.verdict}
    for field in ("fb", "note"):
        value = getattr(args, field) or (old.get(field) if args.keep else None)
        if value:
            new[field] = str(value)
    if args.fix:
        new["fix"] = args.fix
    entries[skill] = new

    path.write_text(header + render_entries(entries), encoding="utf-8", newline="\n")
    print(f"{LEDGER.as_posix()}: {skill} -> " + ", ".join(f"{k}={v}" for k, v in new.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
