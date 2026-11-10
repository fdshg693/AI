#!/usr/bin/env python3
"""Freeze the initial version of a plan folder into its own snapshot/ subfolder.

Usage:
    uv run plans/snapshot_plan.py plans/{plan-name}
    python plans/snapshot_plan.py plans/{plan-name}

Why this exists:
    Plan files are edited while the plan is executed. Because they are updated in
    place, the initial plan can become hard to recover. This script copies the
    plan files that sit directly under a plan folder (`00-overview.md`, `01-*.md`,
    ... for multi-step plans) into `<plan-folder>/snapshot/` verbatim.

    After the snapshot is taken, `snapshot/` is frozen: never edit it. Keep
    editing only the plan files in the parent folder. The frozen copy is the
    AS-IS initial plan, so the live plan can be rewritten freely.

    Take the snapshot once, right after the initial plan review and before the
    first execution step (overview status is planning-* or ready); otherwise it is
    refused. `--allow-late` takes it anyway after execution started (e.g. when a
    single-file plan is moved into a folder) and records in snapshot/README.md that
    it is not the initial plan. `--force` re-takes an existing snapshot, allowed only
    before execution starts. Only NN-*.md plan files are copied, and the copies are
    made read-only. `rough/` and `progress/` are not copied: the snapshot is only
    about the initial plan.

Only the standard library is used, so this script also runs with plain `python`.
"""

import argparse
import os
import re
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path

SNAPSHOT_DIR_NAME = "snapshot"
MANIFEST_NAME = "README.md"
# Plan files only: 00-overview.md, 01-*.md, ... (README.md etc. are not frozen).
PLAN_FILE_PATTERN = re.compile(r"^\d{2}-.+\.md$")
# The initial snapshot (and --force) belong before execution starts.
BEFORE_EXECUTION_STATUSES = {"planning-research", "planning-breakdown", "ready"}
LATE_NOTE = "\n>\n> **実行開始後に取得（初版ではない）。** 取得時点の overview status: `{status}`\n>"

MANIFEST_TEMPLATE = """# snapshot/ - `{plan_name}` の初版プラン凍結コピー

> これは `{plan_name}` の初版プランを {created} に凍結したコピーです。**編集しないでください。**{late_note}
> 実装中に更新するのは親フォルダ側のプラン（`../*.md`）です。
>
> 初版との差分は、プランフォルダを cwd にして次で確認できます。
>
> ```bash
> git diff --no-index snapshot/00-overview.md 00-overview.md
> ```

## 凍結時点のファイル

{files}
"""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "plan_dir",
        type=Path,
        help="スナップショットを取るプランフォルダ（例: plans/{plan-name}）",
    )
    parser.add_argument(
        "--allow-late",
        action="store_true",
        help="実行開始後でも取得する（初版ではない旨を snapshot/README.md に記録する）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="既存の snapshot/ を作り直す（実行着手前のみ許可）",
    )
    return parser.parse_args()


def read_status(path):
    """Return the frontmatter `status` of a plan file, or None."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match:
        return None
    status = re.search(r"^status:\s*([\w-]+)", match.group(1), re.MULTILINE)
    return status.group(1) if status else None


def make_read_only(path):
    path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def remove_tree(path):
    def on_error(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onerror=on_error)


def main():
    args = parse_args()
    plan_dir = args.plan_dir

    if not plan_dir.is_dir():
        print(f"error: plan folder not found: {plan_dir}", file=sys.stderr)
        return 1

    plan_files = sorted(
        path
        for path in plan_dir.glob("*.md")
        if path.is_file() and PLAN_FILE_PATTERN.match(path.name)
    )
    if not plan_files:
        print(
            f"error: no plan files (NN-*.md) directly under: {plan_dir}",
            file=sys.stderr,
        )
        return 1

    overview = plan_dir / "00-overview.md"
    status = read_status(overview) if overview.is_file() else None
    started = status is not None and status not in BEFORE_EXECUTION_STATUSES

    snapshot_dir = plan_dir / SNAPSHOT_DIR_NAME
    if snapshot_dir.exists():
        if not args.force:
            print(
                f"error: {snapshot_dir} already exists. snapshot/ is immutable; "
                "use --force only if execution has not started yet.",
                file=sys.stderr,
            )
            return 1
        if started:
            print(
                f"error: --force refused: {overview.name} status is '{status}' "
                "(execution already started). snapshot/ must stay frozen.",
                file=sys.stderr,
            )
            return 1
        remove_tree(snapshot_dir)
    elif started and not args.allow_late:
        print(
            f"error: {overview.name} status is '{status}' (execution already started), "
            "so this would not be the initial plan. Use --allow-late to take it anyway.",
            file=sys.stderr,
        )
        return 1

    snapshot_dir.mkdir(parents=True)
    for path in plan_files:
        dest = snapshot_dir / path.name
        shutil.copy2(path, dest)
        make_read_only(dest)

    manifest = MANIFEST_TEMPLATE.format(
        plan_name=plan_dir.name,
        created=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S (UTC%z)"),
        late_note=LATE_NOTE.format(status=status) if started else "",
        files="\n".join(f"- `{path.name}`" for path in plan_files),
    )
    manifest_path = snapshot_dir / MANIFEST_NAME
    manifest_path.write_text(manifest, encoding="utf-8")
    make_read_only(manifest_path)

    print(f"snapshot created: {snapshot_dir}")
    for path in plan_files:
        print(f"  frozen: {path.name}")
    print("\nkeep editing the plan files in the parent folder; do not edit snapshot/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
