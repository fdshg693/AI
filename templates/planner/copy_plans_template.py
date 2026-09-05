#!/usr/bin/env python3
"""Copy this repo's .claude/plans/ portable template into another project's CWD.

Usage:
    cd /path/to/target-project
    python /path/to/ai/templates/planner/copy_plans_template.py [--dest DIR] [--force] [--no-claude]

Source of truth is this repo's `.claude/plans/` portable set (AGENTS_GENERAL.md,
copied as AGENTS.md; references/skills-general/, kept under that name since
AGENTS.md's own links point at it; references/{00,01,02,03}-*-example.md,
references/rough/, references/progress/). This repo's own AGENTS.md/README.md/
references/skills/ are intentionally NOT copied — they assume this repo's own
skill/tool conventions. See ../../.claude/plans/COPYING.md for the manual copy
steps this script automates.
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PLANS_DIR = REPO_ROOT / ".claude" / "plans"

# (source path relative to SOURCE_PLANS_DIR, destination path relative to dest .claude/plans/)
COPY_ITEMS = [
    ("AGENTS_GENERAL.md", "AGENTS.md"),
    # Folder name is NOT renamed: AGENTS_GENERAL.md's own links point at
    # "references/skills-general/" by relative path, so renaming the folder
    # without rewriting those links would break them post-copy.
    ("references/skills-general", "references/skills-general"),
    ("references/00-overview-example.md", "references/00-overview-example.md"),
    ("references/01-research-step-example.md", "references/01-research-step-example.md"),
    (
        "references/02-implementation-step-example.md",
        "references/02-implementation-step-example.md",
    ),
    ("references/03-single-file-example.md", "references/03-single-file-example.md"),
    ("references/rough", "references/rough"),
    ("references/progress", "references/progress"),
]
# CLAUDE.md is only needed for Claude Code projects; copied unless --no-claude.
CLAUDE_MD_ITEM = ("CLAUDE.md", "CLAUDE.md")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path.cwd(),
        help="コピー先プロジェクトのルート（デフォルト: カレントディレクトリ）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="コピー先に同名ファイル/フォルダが既にある場合も上書きする",
    )
    parser.add_argument(
        "--no-claude",
        action="store_true",
        help="CLAUDE.md をコピー対象から外す（Claude Code を使わない導入先向け）",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not SOURCE_PLANS_DIR.is_dir():
        print(f"error: source not found: {SOURCE_PLANS_DIR}", file=sys.stderr)
        return 1

    items = list(COPY_ITEMS)
    if not args.no_claude:
        items.append(CLAUDE_MD_ITEM)

    dest_plans_dir = args.dest / ".claude" / "plans"

    # Pre-flight: check all conflicts before copying anything, so a failure
    # never leaves a partial copy behind.
    if not args.force:
        conflicts = [
            dest_plans_dir / dest_name
            for _, dest_name in items
            if (dest_plans_dir / dest_name).exists()
        ]
        if conflicts:
            print("error: destination already exists (use --force to overwrite):", file=sys.stderr)
            for path in conflicts:
                print(f"  {path}", file=sys.stderr)
            return 1

    dest_plans_dir.mkdir(parents=True, exist_ok=True)

    for src_name, dest_name in items:
        src = SOURCE_PLANS_DIR / src_name
        dest = dest_plans_dir / dest_name

        if not src.exists():
            print(f"warning: skip missing source item: {src}", file=sys.stderr)
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=args.force)
        else:
            shutil.copy2(src, dest)
        print(f"copied: {src} -> {dest}")

    print(
        f"\ndone. next: adjust skill links / rule-storage references in {dest_plans_dir} "
        "for this project's conventions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
