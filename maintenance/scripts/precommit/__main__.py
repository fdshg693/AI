"""Single pre-commit entry for the maintenance/scripts Python jobs.

lefthook used to start one `just` -> `powershell` -> `uv run python` chain per
job (~1s of process startup each, ~15 jobs). This runs the same modules
in-process instead, in a fixed dependency order:

    fix   — SKILL.md meta defaults -> generated catalogs/marketplaces -> tool
            manifest version bumps (all write files; lefthook re-stages them)
    check — read-only checks (SKILL.md version bump, repo-tools consistency)

Each task still runs only when a staged path matches its globs (the same globs
lefthook used per job). `--all` ignores the staged list and runs every task,
e.g. for a manual regeneration outside a commit.

Run via `just --justfile maintenance/scripts/justfile precommit-fix|precommit-check`.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import repo_git

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Task:
    name: str
    module: str
    globs: tuple[str, ...]
    # Tasks whose outputs this one reads: if any of them ran, this one runs too.
    after: tuple[str, ...] = ()
    # How to call the module's main(): "none" -> main(), "argv" -> main([module]),
    # "list" -> main([]) (argparse mains that would otherwise read sys.argv).
    call: str = "none"


SKILL_MD = ("**/SKILL.md",)
# Submodule gitlinks as staged in the umbrella by a pointer update. The files
# inside were already handled by the submodule's own pre-commit; the umbrella
# only refreshes the aggregate outputs it owns (marketplaces, skill-catalog.json).
GITLINKS = ("skills", "tools", "agent-compat")

FIX_TASKS = (
    # SKILL.md meta defaults first: the catalog generators below read the frontmatter.
    Task("skill-versions", "skill.set.set_skill_versions", SKILL_MD),
    Task("skill-descriptions", "skill.set.set_skill_descriptions", SKILL_MD),
    Task("skill-tags", "skill.set.set_skill_tags", SKILL_MD),
    Task(
        "marketplace",
        "plugin_meta.generate.generate_marketplace",
        ("**/.claude-plugin/plugin.json", "registry/ai-tools.yaml", *GITLINKS),
    ),
    Task(
        "codex-marketplace",
        "plugin_meta.generate.generate_codex_marketplace",
        ("**/.codex-plugin/plugin.json", "registry/ai-tools.yaml", *GITLINKS),
    ),
    Task(
        "copilot-marketplace",
        "plugin_meta.generate.generate_copilot_marketplace",
        ("**/plugin.json", "registry/ai-tools.yaml", *GITLINKS),
    ),
    Task(
        # Gitignored output: refreshing it never adds files to the commit.
        "workspace-copies",
        "plugin_meta.generate.generate_workspace_copies",
        ("skills/plugins/ai-tools-knowledge/**", "registry/ai-tools.yaml", *GITLINKS),
    ),
    Task(
        "skill-catalog",
        "plugin_meta.generate.generate_skill_catalog",
        ("**/skills/**", ".claude-plugin/marketplace.json", "registry/ai-tools.yaml", *GITLINKS),
        after=("marketplace",),
    ),
    Task(
        "skills-catalog-md",
        "plugin_meta.generate.generate_skills_catalog_md",
        ("**/skills/**", "registry/ai-tools.yaml"),
    ),
    Task(
        "readme-tools-section",
        "plugin_meta.generate.generate_readme_tools_section",
        ("registry/ai-tools.yaml",),
    ),
    Task(
        "skills-plugin-index",
        "plugin_meta.generate.generate_skills_plugin_index",
        (),  # Explicit generation or CI --all; hooks validate without writing across repositories.
    ),
    Task(
        "registry-compat",
        "plugin_meta.generate.generate_registry_compat",
        (
            "registry/*.yaml",
            # A hand edit of a root copy is overwritten from registry/.
            "ai-tools.yaml",
            "repo-tools.yaml",
            "repo-workflows.yaml",
            "repo-hooks.yaml",
        ),
    ),
    Task("tool-version-bump", "release.bump_tool_versions", ("tools/**",), call="list"),
)

CHECK_TASKS = (
    Task(
        "skill-version-bump-check",
        "skill.check.check_skill_version_bump",
        SKILL_MD,
        call="argv",
    ),
    Task(
        "skill-repo-tools-check",
        "skill.check.check_skill_repo_tools",
        (
            "**/SKILL.md",
            "registry/repo-tools.yaml",
            "tools/**/pyproject.toml",
            "tools/**/package.json",
        ),
        call="argv",
    ),
    Task(
        "repo-tool-relations-check",
        "skill.check.check_repo_tool_relations",
        (
            "**/SKILL.md",
            "registry/repo-tools.yaml",
            "tools/**/pyproject.toml",
            "tools/**/package.json",
        ),
        call="argv",
    ),
)

PHASES = {"fix": FIX_TASKS, "check": CHECK_TASKS}


def staged_files() -> list[PurePosixPath]:
    try:
        staged = repo_git.staged_files(REPO_ROOT, include_deleted=True)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
    return [PurePosixPath(line) for line in staged]


def matches(task: Task, paths: list[PurePosixPath]) -> bool:
    return any(path.full_match(glob) for path in paths for glob in task.globs)


def select(tasks: tuple[Task, ...], paths: list[PurePosixPath] | None) -> list[Task]:
    if paths is None:
        return list(tasks)
    selected: list[Task] = []
    names: set[str] = set()
    for task in tasks:
        if matches(task, paths) or names.intersection(task.after):
            selected.append(task)
            names.add(task.name)
    return selected


def invoke(task: Task) -> int:
    main: Callable[..., int | None] = importlib.import_module(task.module).main
    try:
        if task.call == "argv":
            result = main([task.module])
        elif task.call == "list":
            result = main([])
        else:
            result = main()
    except SystemExit as exc:
        if exc.code is None or exc.code == 0:
            return 0
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            return 1
        return int(exc.code)
    return result or 0


def run(tasks: list[Task]) -> int:
    failed: list[str] = []
    for task in tasks:
        started = time.perf_counter()
        code = invoke(task)
        elapsed = time.perf_counter() - started
        status = "ok" if code == 0 else f"FAILED ({code})"
        print(f"[precommit] {task.name}: {status} in {elapsed:.2f}s", flush=True)
        if code != 0:
            failed.append(task.name)
    if failed:
        print(f"[precommit] failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("phase", choices=sorted(PHASES))
    parser.add_argument(
        "--all", action="store_true", help="run every task regardless of staged files"
    )
    args = parser.parse_args(argv)
    paths = None if args.all else staged_files()
    return run(select(PHASES[args.phase], paths))


if __name__ == "__main__":
    sys.exit(main())
