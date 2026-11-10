"""Repository-wide pytest hooks.

pytest walks into Windows junctions (and does not stop at one pointing at an
ancestor), so collection skips any symlink or junction directory. Junctions are
declared in .links.yaml; see docs/repo-wide/repo-layout.md.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

_MOUNT_POINT = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)


def _is_link_like(path: Path) -> bool:
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    return getattr(st, "st_reparse_tag", 0) == _MOUNT_POINT


def pytest_ignore_collect(collection_path: Path, config) -> bool | None:
    if collection_path.is_dir() and _is_link_like(collection_path):
        return True
    return None
