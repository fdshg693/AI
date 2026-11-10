"""CLI: ``python -m branches status|list|new|switch|delete|push|pull``.

Runs on the umbrella and every checked-out submodule. ``--only SUB ...`` limits
the submodules (the umbrella is always included).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from branches import core


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="branches", description=__doc__)
    parser.add_argument(
        "--root", type=Path, help="umbrella root (default: from the current directory)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, help_: str, *, branch: bool = False) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_)
        if branch:
            p.add_argument("name", help="branch name")
        p.add_argument(
            "--only", nargs="+", metavar="SUB", help="only these submodules (plus the umbrella)"
        )
        return p

    add("status", "branch, upstream, dirty and pointer state of every repository")
    add("list", "local branches across repositories")
    p = add("new", "create a branch and switch to it everywhere", branch=True)
    p.add_argument("--from", dest="base", help="start point (default: each repository's HEAD)")
    p = add("switch", "switch everywhere (local or origin/<name>)", branch=True)
    p.add_argument("--create", action="store_true", help="create it where it does not exist")
    p.add_argument("--no-fetch", action="store_true", help="do not fetch origin first")
    p = add("delete", "delete a branch everywhere it exists", branch=True)
    p.add_argument("--force", action="store_true", help="delete even if unmerged (git branch -D)")
    p.add_argument("--remote", action="store_true", help="also delete origin/<name>")
    add("push", "push current branches, submodules before the umbrella")
    add("pull", "fast-forward current branches from their upstream, keeping branches")

    args = parser.parse_args(argv)
    try:
        root = (args.root or core.find_root(Path.cwd())).resolve()
        if args.command == "status":
            return core.status(root, args.only)
        if args.command == "list":
            return core.list_branches(root, args.only)
        if args.command == "new":
            return core.new(root, args.name, args.only, args.base)
        if args.command == "switch":
            return core.switch(root, args.name, args.only, args.create, not args.no_fetch)
        if args.command == "delete":
            return core.delete(root, args.name, args.only, args.force, args.remote)
        if args.command == "push":
            return core.push(root, args.only)
        return core.pull(root, args.only)
    except core.BranchError as exc:
        print(f"error: {exc}\nnothing was changed", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"error: {' '.join(exc.cmd)}: {exc.stderr}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
