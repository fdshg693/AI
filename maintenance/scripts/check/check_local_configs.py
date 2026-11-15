"""Check that local config files stay untracked and only their examples are committed.

Reads ``registry/local-configs.yaml`` and the index (``git ls-files``) of the
umbrella and every checked-out submodule, then reports:

1. a declared real file (``local_configs[].path``) that is tracked or not gitignored
2. a declared example (``local_configs[].example``) that is not tracked
3. a tracked example ``X.example.Y`` / ``X.Y.example`` whose real file ``X.Y`` is tracked
4. a tracked file matching ``deny_patterns`` that is not in ``allow_tracked``

plus ``allow_tracked`` entries that are no longer tracked (stale declarations).

Wired into ``precommit check`` (every commit) and CI; run manually with
``just --justfile maintenance/scripts/justfile local-configs-check``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml

import repo_git

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "registry" / "local-configs.yaml"
EXAMPLE = "example"


@dataclass(frozen=True)
class LocalConfig:
    path: str
    example: str


@dataclass(frozen=True)
class Config:
    local_configs: tuple[LocalConfig, ...]
    deny_patterns: tuple[str, ...]
    allow_tracked: tuple[str, ...]


def _entries(data: dict, key: str, fields: tuple[str, ...]) -> list[dict]:
    items = data.get(key) or []
    if not isinstance(items, list):
        raise ValueError(f"{key}: must be a list")
    for item in items:
        if not isinstance(item, dict) or any(not isinstance(item.get(f), str) for f in fields):
            raise ValueError(f"{key}: each entry needs string fields {', '.join(fields)}")
    return items


def load_config(path: Path = CONFIG_PATH) -> Config:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    patterns = data.get("deny_patterns") or []
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise ValueError("deny_patterns: must be a list of strings")
    return Config(
        local_configs=tuple(
            LocalConfig(item["path"], item["example"])
            for item in _entries(data, "local_configs", ("path", "example", "reason"))
        ),
        deny_patterns=tuple(patterns),
        allow_tracked=tuple(
            item["path"] for item in _entries(data, "allow_tracked", ("path", "reason"))
        ),
    )


def is_example_name(name: str) -> bool:
    """``X.example.Y`` or ``X.Y.example`` (the first segment is the stem, never the marker)."""
    return EXAMPLE in name.split(".")[1:]


def real_name(name: str) -> str:
    """The real file name an example name stands for: drop the ``example`` segment."""
    parts = name.split(".")
    index = parts.index(EXAMPLE, 1)
    return ".".join(parts[:index] + parts[index + 1 :])


def find_violations(
    config: Config,
    tracked: Iterable[str],
    is_ignored: Callable[[list[str]], set[str]],
) -> list[str]:
    """Return ``path: reason`` lines. ``is_ignored`` maps paths to the ignored subset."""
    tracked_set = set(tracked)
    violations: list[str] = []

    real_paths = [entry.path for entry in config.local_configs]
    ignored = is_ignored(real_paths) if real_paths else set()
    for entry in config.local_configs:
        if entry.path in tracked_set:
            violations.append(
                f"{entry.path}: local config is tracked (git rm --cached it; "
                f"commit {entry.example} instead)"
            )
        if entry.path not in ignored:
            violations.append(f"{entry.path}: local config is not gitignored")
        if entry.example not in tracked_set:
            violations.append(f"{entry.example}: example of {entry.path} is not tracked")

    for path in sorted(tracked_set):
        pure = PurePosixPath(path)
        if not is_example_name(pure.name):
            continue
        real = pure.with_name(real_name(pure.name)).as_posix()
        if real in tracked_set:
            violations.append(f"{real}: tracked next to its example {path}")

    allowed = set(config.allow_tracked)
    for path in sorted(tracked_set):
        pure = PurePosixPath(path)
        if path in allowed or is_example_name(pure.name):
            continue
        hit = next((g for g in config.deny_patterns if pure.full_match(g)), None)
        if hit is not None:
            violations.append(
                f"{path}: tracked file matches deny pattern {hit} "
                "(commit an example instead, or add it to allow_tracked with a reason)"
            )

    for path in config.allow_tracked:
        if path not in tracked_set:
            violations.append(f"{path}: listed in allow_tracked but not tracked (remove the entry)")

    return list(dict.fromkeys(violations))


def check(root: Path, config: Config) -> list[str]:
    return find_violations(
        config,
        repo_git.tracked_files(root),
        lambda paths: repo_git.ignored_files(root, paths),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args(argv)
    try:
        violations = check(REPO_ROOT, load_config(args.config))
    except (OSError, ValueError, yaml.YAMLError, RuntimeError) as exc:
        print(f"check_local_configs: {exc}", file=sys.stderr)
        return 1
    if not violations:
        return 0
    print("Local config violations (see registry/local-configs.yaml):", file=sys.stderr)
    for line in violations:
        print(f"  {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
