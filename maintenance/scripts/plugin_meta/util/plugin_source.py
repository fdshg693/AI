"""Where a marketplace entry should fetch a plugin from.

Plugins inside a submodule (skills/, tools/) cannot be reached by a relative
path from the umbrella's marketplace without recursive submodule clones, which
older clients skip (repo-restructure research 01-D, removed; see git history). Their entries point at the
submodule's own GitHub repository instead, unpinned (the repository's default
branch), so an entry never names a commit that has not been pushed yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import repo_git

_GITHUB = "https://github.com/"


@dataclass(frozen=True)
class RemotePlugin:
    url: str  # https clone URL ending in .git
    repo: str  # owner/repo
    path: str  # plugin dir inside that repository


def remote_plugin(root: Path, rel_posix: str) -> RemotePlugin | None:
    """The submodule repository holding ``rel_posix``, or None for umbrella paths."""
    urls = repo_git.submodule_urls(root)
    for sub in sorted(urls, key=len, reverse=True):
        if rel_posix == sub or rel_posix.startswith(f"{sub}/"):
            url = urls[sub]
            if not url.startswith(_GITHUB):
                raise ValueError(f"submodule {sub} is not an https GitHub URL: {url}")
            repo = url[len(_GITHUB) :].removesuffix(".git").strip("/")
            inner = rel_posix[len(sub) + 1 :] if rel_posix != sub else "."
            return RemotePlugin(url=f"{_GITHUB}{repo}.git", repo=repo, path=inner)
    return None
