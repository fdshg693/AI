"""List relative Markdown links in tracked files whose target does not exist.

Used around path moves: save a baseline before ``git mv`` and diff it after the
rewrite, so only breakage introduced by the move shows up::

    uv run python -m reorg.check_links > before.txt
    ... git mv / rewrite ...
    uv run python -m reorg.check_links > after.txt
"""

from __future__ import annotations

import posixpath
import sys

from reorg.rewrite_moved_paths import LINK_RE, SCHEME_RE, git, repo_root


def main() -> int:
    root = repo_root()
    tracked = git(root, "ls-files", "-z").split("\0")
    existing = set(tracked)
    for f in tracked:
        parts = f.split("/")
        for i in range(1, len(parts)):
            existing.add("/".join(parts[:i]))
    broken = []
    for rel in tracked:
        if not rel.endswith(".md") or rel.startswith(".claude/hooks/"):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        base = posixpath.dirname(rel)
        for m in LINK_RE.finditer(text):
            target = m.group(2)
            if SCHEME_RE.match(target) or target.startswith(("/", "$", "{")):
                continue
            resolved = posixpath.normpath(posixpath.join(base, target.replace("%20", " ")))
            if resolved.startswith("..") or resolved in existing or (root / resolved).exists():
                continue
            broken.append(f"{rel} -> {target}")
    for item in sorted(broken):
        print(item)
    print(f"# {len(broken)} broken", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
