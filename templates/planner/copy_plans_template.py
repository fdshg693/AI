#!/usr/bin/env python3
"""Copy this repo's .claude/plans/ template into another project's CWD.

Usage:
    cd /path/to/target-project
    python /path/to/ai/templates/planner/copy_plans_template.py [--dest DIR] [--force]

Source of truth is this repo's `.claude/plans/` (AGENTS.md, CLAUDE.md,
README.md, references/). See templates/planner/README.md for the manual
copy steps this script automates.
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PLANS_DIR = REPO_ROOT / ".claude" / "plans"
COPY_ITEMS = ["AGENTS.md", "CLAUDE.md", "README.md", "references"]


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
    return parser.parse_args()


def main():
    args = parse_args()

    if not SOURCE_PLANS_DIR.is_dir():
        print(f"error: source not found: {SOURCE_PLANS_DIR}", file=sys.stderr)
        return 1

    dest_plans_dir = args.dest / ".claude" / "plans"

    # Pre-flight: check all conflicts before copying anything, so a failure
    # never leaves a partial copy behind.
    if not args.force:
        conflicts = [
            dest_plans_dir / name for name in COPY_ITEMS if (dest_plans_dir / name).exists()
        ]
        if conflicts:
            print("error: destination already exists (use --force to overwrite):", file=sys.stderr)
            for path in conflicts:
                print(f"  {path}", file=sys.stderr)
            return 1

    dest_plans_dir.mkdir(parents=True, exist_ok=True)

    for name in COPY_ITEMS:
        src = SOURCE_PLANS_DIR / name
        dest = dest_plans_dir / name

        if not src.exists():
            print(f"warning: skip missing source item: {src}", file=sys.stderr)
            continue

        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=args.force)
        else:
            shutil.copy2(src, dest)
        print(f"copied: {src} -> {dest}")

    print(
        f"\ndone. next: adjust rule-storage references in {dest_plans_dir} for this project's conventions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
