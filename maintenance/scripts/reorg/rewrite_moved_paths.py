"""Rewrite path references after a batch of ``git mv`` moves.

Run from ``maintenance/scripts`` (or wherever this package lives) after staging
the moves with ``git mv`` and before committing::

    uv run python -m reorg.rewrite_moved_paths reorg/tables/<batch>.json
    uv run python -m reorg.rewrite_moved_paths reorg/tables/<batch>.json --dry-run

The table is a JSON object ``{"moves": [[old_prefix, new_prefix], ...],
"exclude": [repo-relative prefixes to leave untouched]}``. Prefixes are POSIX,
repo-root relative, without a trailing slash.

What it rewrites in every tracked text file (``git ls-files``, so junctions and
ignored files are never touched):

1. Relative Markdown links ``](path)``. The link is resolved against the file's
   location *before* the move (HEAD), mapped through the table, and recomputed
   from the file's location *after* the move. Only links whose target existed in
   HEAD are touched. This also fixes ``../`` depth changes inside moved files.
2. Repo-root-relative mentions of an old prefix (``tools/internal/x``,
   ``tools\\internal\\x``). The prefix must not be preceded by a path character,
   so ``../../docs/repo-wide`` style relative paths outside Markdown links are
   left for manual review (``--report-relative`` lists them).

A ``SKILL.md`` whose content changed gets its ``meta.version`` patch-bumped,
matching ``check_skill_version_bump``. Line endings are preserved.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path

BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".lock",
    ".pyc",
    ".zip",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".sqlite",
    ".db",
}
ALWAYS_EXCLUDE = (".claude/hooks/",)
VERSION_RE = re.compile(r"(?m)^(\s*version:\s*)(\d+(?:\.\d+)*)([^\n]*)$")
LINK_RE = re.compile(r"\]\(\s*(<?)([^)\s>#]+)(>?)((?:#[^)\s]*)?)(\s+\"[^\"]*\")?\s*\)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
PATH_CHAR = r"[\w.\-/\\@]"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def repo_root() -> Path:
    return Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())


def load_table(path: Path) -> tuple[list[tuple[str, str]], tuple[str, ...]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    moves = [(old.strip("/"), new.strip("/")) for old, new in data["moves"]]
    moves.sort(key=lambda m: len(m[0]), reverse=True)
    exclude = tuple(data.get("exclude", ()))
    return moves, exclude


def map_prefix(path: str, moves: list[tuple[str, str]], reverse: bool = False) -> str:
    for old, new in moves:
        src, dst = (new, old) if reverse else (old, new)
        if path == src:
            return dst
        if path.startswith(src + "/"):
            return dst + path[len(src) :]
    return path


def old_tree_paths(root: Path) -> set[str]:
    files = git(root, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    paths = set(files)
    for f in files:
        parts = f.split("/")
        for i in range(1, len(parts)):
            paths.add("/".join(parts[:i]))
    return paths


def rewrite_links(
    text: str, new_file: str, old_file: str, moves: list[tuple[str, str]], old_paths: set[str]
) -> str:
    new_dir = posixpath.dirname(new_file)
    old_dir = posixpath.dirname(old_file)

    def repl(match: re.Match[str]) -> str:
        target = match.group(2)
        if SCHEME_RE.match(target) or target.startswith(("/", "$", "{")):
            return match.group(0)
        trailing = "/" if target.endswith("/") else ""
        decoded = target.replace("%20", " ")
        old_target = posixpath.normpath(posixpath.join(old_dir, decoded))
        if old_target.startswith("..") or old_target not in old_paths:
            return match.group(0)
        new_target = map_prefix(old_target, moves)
        if new_target == old_target and new_dir == old_dir:
            return match.group(0)
        rel = posixpath.relpath(new_target, new_dir or ".")
        if rel == ".":
            rel = "./"
        elif not trailing and target.startswith("./") and not rel.startswith("."):
            rel = "./" + rel
        rel = rel + trailing if not rel.endswith("/") else rel
        if " " in decoded and "%20" in target:
            rel = rel.replace(" ", "%20")
        if rel.rstrip("/") == target.rstrip("/").removeprefix("./") or rel == target:
            return match.group(0)
        start, end = match.span(2)
        whole_start = match.start(0)
        s = match.group(0)
        return s[: start - whole_start] + rel + s[end - whole_start :]

    return LINK_RE.sub(repl, text)


def build_prefix_pattern(moves: list[tuple[str, str]]) -> tuple[re.Pattern[str], dict[str, str]]:
    """One alternation (longest first) so a replaced prefix is never re-matched."""
    lookup: dict[str, str] = {}
    for old, new in moves:
        for sep in ("/", "\\"):
            lookup[old.replace("/", sep)] = new.replace("/", sep)
    alternation = "|".join(re.escape(o) for o in sorted(lookup, key=len, reverse=True))
    pattern = re.compile(rf"(?<!{PATH_CHAR})(?:{alternation})(?=$|[^\w\-.]|\.(?:$|[^\w]))")
    return pattern, lookup


def rewrite_prefixes(text: str, pattern: re.Pattern[str], lookup: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        old = m.group(0)
        new = lookup[old]
        if "/" not in old and "\\" not in old:
            # Single-segment prefix: follow the separator style of the text after it.
            following = m.string[m.end() : m.end() + 1]
            new = new.replace("/", "\\") if following == "\\" else new.replace("\\", "/")
        return new

    return pattern.sub(repl, text)


def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    return text[: end + 4], text[end + 4 :]


def bump_version(frontmatter: str) -> str:
    def repl(match: re.Match[str]) -> str:
        parts = match.group(2).split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return f"{match.group(1)}{'.'.join(parts)}"

    return VERSION_RE.sub(repl, frontmatter, count=1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("table", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--report-relative",
        action="store_true",
        help="list ../-style mentions of old prefixes that were not rewritten",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    moves, exclude = load_table(args.table)
    exclude = ALWAYS_EXCLUDE + exclude
    old_paths = old_tree_paths(root)
    pattern, lookup = build_prefix_pattern(moves)
    changed: list[str] = []
    bumped: list[str] = []
    leftovers: list[str] = []

    for rel in git(root, "ls-files", "-z").split("\0"):
        if not rel or rel.startswith(exclude):
            continue
        path = root / rel
        if path.suffix.lower() in BINARY_SUFFIXES or not path.is_file():
            continue
        try:
            raw = path.read_bytes()
            original = raw.decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        newline = "\r\n" if b"\r\n" in raw else "\n"
        text = original.replace("\r\n", "\n")
        old_rel = map_prefix(rel, moves, reverse=True)
        updated = rewrite_links(text, rel, old_rel, moves, old_paths)
        updated = rewrite_prefixes(updated, pattern, lookup)
        if args.report_relative:
            for old, _ in moves:
                for line_no, line in enumerate(updated.splitlines(), 1):
                    for sep in ("/", "\\"):
                        if re.search(rf"\.\.[/\\]{re.escape(old.replace('/', sep))}", line) or (
                            re.search(rf"[/\\]{re.escape(old.replace('/', sep))}\b", line)
                            and "../" in line
                        ):
                            leftovers.append(f"{rel}:{line_no}: {line.strip()[:160]}")
        if path.name == "SKILL.md" and updated != text:
            # check_skill_version_bump rejects any content change without a bump.
            new_fm, new_body = split_frontmatter(updated)
            if new_fm:
                updated = bump_version(new_fm) + new_body
                bumped.append(rel)
        if updated != text:
            changed.append(rel)
            if not args.dry_run:
                path.write_bytes(updated.replace("\n", newline).encode("utf-8"))

    print(f"changed {len(changed)}")
    for item in changed:
        print(f"  {item}")
    print(f"bumped {len(bumped)}")
    for item in bumped:
        print(f"  {item}")
    if args.report_relative:
        print(f"relative leftovers {len(leftovers)}")
        for item in sorted(set(leftovers)):
            print(f"  {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
