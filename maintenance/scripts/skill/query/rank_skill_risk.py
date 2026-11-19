"""Rank skills by how likely they are to be broken or stale ("risk").

Read-only. Not wired into lefthook — invoke from the ``skill-risk`` just recipe
when choosing which skill to dogfood next.

Targets are the SKILL.md files under the four plugin roots (``TARGET_ROOTS``),
minus nested parts (a SKILL.md whose ancestor directory under the same root also
has one) and, unless ``--include-deprecated``, ``meta.status: deprecated``.

Factors per skill (all shown in the output, so the order can be explained):

- last change: newest substantive commit touching the skill directory (git, one
  ``git log`` per repository; bulk commits are skipped, see ``is_bulk_commit``).
  A skill with no substantive commit since the import is "baseline" and its age
  counts from ``BASELINE_DATE``. A skill whose repository cannot be read is
  "unknown" and gets ``UNKNOWN_POINTS``.
- churn: substantive commits in the last ``CHURN_WINDOW_DAYS`` days.
- last dogfooding: ``maintenance/skill-risk/dogfood.yaml`` (missing = never).
- volatility: ``maintenance/skill-risk/volatility.yaml`` (overrides, then the
  longest prefix rule, then ``default`` reported as "no rule").
- changed dependencies: ``requires_repo_tools`` / ``requires_skills`` targets
  changed after the skill's last change.
- open fb: ``skill-tools --fb`` files newer than the last dogfooding. fb is
  terminal-local (gitignored), so this factor can differ between machines.
  Skills missing from the skill catalog cannot receive fb ("n/a").

The score formula lives in the constants below; change weights there.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

import repo_git
from skill.util.repo_tools_registry import REPO_ROOT, load_repo_tools
from skill.util.skill_frontmatter import find_skill_md_files, read_frontmatter
from skill.util.skill_tool_graph import SkillNode, SkillToolGraph, load_graph

# --- scope -----------------------------------------------------------------

TARGET_ROOTS = (
    "skills/plugins/",
    "tools/_plugin/",
    "agent-compat/_plugin/",
    "maintenance/plugin/",
)

VOLATILITY_PATH = "maintenance/skill-risk/volatility.yaml"
DOGFOOD_PATH = "maintenance/skill-risk/dogfood.yaml"
CATALOG_PATH = ".claude-plugin/skill-catalog.json"
FB_SKILLS_DIR = "tools/skill-tools/fb/skills"

# --- git history -------------------------------------------------------------

# Both the umbrella and the submodules start on this day (import / move); older
# history does not exist anywhere. A skill without a substantive commit since
# then is "baseline" and ages from this date.
BASELINE_DATE = date(2026, 11, 10)
# Commits are skipped when the subject starts with one of these or they touch
# more files than BULK_FILE_LIMIT (moves, imports, repo-wide path rewrites).
BULK_SUBJECT_PREFIXES = ("refactor(repo)", "chore(repo): import")
BULK_FILE_LIMIT = 100

# --- score -------------------------------------------------------------------

VOLATILITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}
CHURN_WINDOW_DAYS = 30
CHURN_POINTS = 2  # per substantive commit in the window
CHURN_CAP = 5  # commits counted at most
DEP_CHANGED_POINTS = 5  # per changed dependency
DEP_CHANGED_CAP = 3  # dependencies counted at most
NEVER_DOGFOODED_POINTS = 10
NEEDS_FIX_POINTS = 20  # ledger verdict needs-fix: known broken, not yet fixed
FB_POINTS = 5  # per open fb file
UNKNOWN_POINTS = 50  # last change could not be read: unverifiable is risky

FB_NAME_RE = re.compile(r"^(\d{8})-(\d{6})-fb\.md$")

EPILOG = """\
score = volatility weight x days since the newer of (last change, last dogfooding)
      + churn + changed dependencies + never dogfooded / needs-fix + open fb
      (+ unknown when git history could not be read)

examples:
  just --justfile maintenance/scripts/justfile skill-risk
  just --justfile maintenance/scripts/justfile skill-risk --top 20
  just --justfile maintenance/scripts/justfile skill-risk --json
"""


# --- data --------------------------------------------------------------------


@dataclass
class Commit:
    sha: str
    when: datetime
    subject: str
    files: list[str]


@dataclass
class History:
    """Substantive commits per umbrella-relative directory/file path."""

    by_path: dict[str, set[str]] = field(default_factory=dict)
    commits: dict[str, Commit] = field(default_factory=dict)
    # Umbrella-relative prefixes of repositories whose history could not be read
    # (uninitialized submodule, git failure). "" means the umbrella itself.
    unreadable: set[str] = field(default_factory=set)
    readable: set[str] = field(default_factory=set)

    def is_unknown(self, rel: str) -> bool:
        prefix = repo_prefix_of(rel, self.readable | self.unreadable)
        return prefix in self.unreadable

    def commits_for(self, rel: str) -> list[Commit]:
        shas = self.by_path.get(rel.rstrip("/"), set())
        return sorted((self.commits[s] for s in shas), key=lambda c: c.when)

    def last_change(self, rel: str) -> datetime | None:
        commits = self.commits_for(rel)
        return commits[-1].when if commits else None


@dataclass
class Dependency:
    kind: str  # repo_tool | skill
    token: str
    path: str | None  # umbrella-relative path the date is read from
    state: str  # changed | unchanged | unresolved | ambiguous | unknown
    last_change: str | None = None


@dataclass
class SkillRisk:
    id: str
    name: str
    status: str
    volatility: str
    volatility_source: str  # override | rule | no rule
    last_change: str | None  # ISO date, None for baseline/unknown
    last_change_state: str  # changed | baseline | unknown
    change_age_days: int | None
    churn: int
    dogfood_date: str | None
    dogfood_verdict: str | None
    staleness_days: int | None
    dependencies: list[Dependency]
    changed_dependencies: list[str]
    open_fb: int | None  # None = skill not in catalog (fb not available)
    score: int
    factors: dict[str, int]
    reason: str


# --- enumeration ---------------------------------------------------------------


def target_skill_paths(root: Path) -> list[Path]:
    """SKILL.md files under TARGET_ROOTS, without nested parts."""
    found: list[Path] = []
    for path in find_skill_md_files(root):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(TARGET_ROOTS):
            found.append(path)
    dirs = {p.parent.relative_to(root).as_posix() for p in found}
    result: list[Path] = []
    for path in found:
        rel_dir = PurePosixPath(path.parent.relative_to(root).as_posix())
        plugin_root = next(r for r in TARGET_ROOTS if str(rel_dir).startswith(r))
        nested = any(
            str(anc) in dirs
            for anc in rel_dir.parents
            if f"{anc}/".startswith(plugin_root) and str(anc) != "."
        )
        if not nested:
            result.append(path)
    return result


# --- git -------------------------------------------------------------------------


def repo_prefix_of(rel: str, prefixes: set[str]) -> str:
    """Longest repository prefix ("" = umbrella) owning ``rel``."""
    best = ""
    for prefix in prefixes:
        if prefix and (rel == prefix or rel.startswith(f"{prefix}/")) and len(prefix) > len(best):
            best = prefix
    return best


def is_bulk_commit(subject: str, file_count: int) -> bool:
    return subject.startswith(BULK_SUBJECT_PREFIXES) or file_count > BULK_FILE_LIMIT


def _git_log(repo: Path) -> str | None:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotepath=false",
            "log",
            "--no-renames",
            "--name-only",
            "--format=%x1e%H%x09%cI%x09%s",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def parse_log(text: str) -> list[Commit]:
    commits: list[Commit] = []
    for block in text.split("\x1e"):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        sha, when, subject = (lines[0].split("\t", 2) + ["", ""])[:3]
        commits.append(
            Commit(sha=sha, when=datetime.fromisoformat(when), subject=subject, files=lines[1:])
        )
    return commits


def add_commits(history: History, prefix: str, commits: list[Commit]) -> None:
    for commit in commits:
        if commit.when.date() < BASELINE_DATE:
            continue
        if is_bulk_commit(commit.subject, len(commit.files)):
            continue
        key = f"{prefix}:{commit.sha}"
        history.commits[key] = commit
        for inner in commit.files:
            rel = f"{prefix}/{inner}" if prefix else inner
            path = PurePosixPath(rel)
            history.by_path.setdefault(rel, set()).add(key)
            for parent in path.parents:
                if str(parent) == ".":
                    break
                history.by_path.setdefault(str(parent), set()).add(key)


def load_history(root: Path) -> History:
    history = History()
    checked_out = set(repo_git.submodule_paths(root))
    declared = set(repo_git.submodule_urls(root)) | checked_out
    history.unreadable.update(declared - checked_out)
    for prefix in ["", *sorted(checked_out)]:
        text = _git_log(root / prefix if prefix else root)
        if text is None:
            history.unreadable.add(prefix)
            continue
        history.readable.add(prefix)
        add_commits(history, prefix, parse_log(text))
    return history


# --- inputs ------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def resolve_volatility(skill_id: str, config: dict[str, Any]) -> tuple[str, str]:
    overrides = config.get("overrides") or {}
    entry = overrides.get(skill_id)
    if isinstance(entry, dict) and entry.get("level"):
        return str(entry["level"]), "override"
    best: tuple[int, str] | None = None
    for rule in config.get("rules") or []:
        prefix = rule.get("prefix") if isinstance(rule, dict) else None
        if isinstance(prefix, str) and skill_id.startswith(prefix):
            if best is None or len(prefix) > best[0]:
                best = (len(prefix), str(rule.get("level")))
    if best is not None:
        return best[1], "rule"
    return str(config.get("default", "medium")), "no rule"


def load_catalog_dirs(root: Path) -> set[str] | None:
    path = root / CATALOG_PATH
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    dirs: set[str] = set()
    for key, entries in data.items():
        if key.startswith("_") or not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                dirs.add(entry["path"].rstrip("/"))
    return dirs


def fb_files(root: Path, name: str) -> list[str]:
    folder = root / FB_SKILLS_DIR / name
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if FB_NAME_RE.match(p.name))


def count_open_fb(files: list[str], dogfood: dict[str, Any] | None) -> int:
    if not dogfood:
        return len(files)
    seen_fb = dogfood.get("fb")
    if isinstance(seen_fb, str) and seen_fb:
        return sum(1 for f in files if f > seen_fb)
    day = _as_date(dogfood.get("date"))
    if day is None:
        return len(files)
    stamp = day.strftime("%Y%m%d")
    return sum(1 for f in files if f[:8] > stamp)


def _as_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


# --- dependencies ----------------------------------------------------------------


def resolve_dependencies(
    skill: SkillNode,
    graph: SkillToolGraph,
    history: History,
    root: Path,
    skill_changed: datetime | None,
) -> list[Dependency]:
    deps: list[Dependency] = []
    for token in skill.requires_repo_tools:
        keys = graph.tool_keys_mentioned((token,))
        if keys:
            path: str | None = graph.tools[sorted(keys)[0]].path or None
        else:
            candidate = token.replace("\\", "/").rstrip("/")
            path = candidate if (root / candidate).exists() else None
        deps.append(
            _dated(Dependency("repo_tool", token, path, "unresolved"), history, skill_changed)
        )
    for name in skill.requires_skills:
        if ":" in name:
            continue  # external plugin skill (superpowers:..., etc.)
        candidates = [
            s for s in graph.skills_by_name.get(name, []) if s.rel_posix != skill.rel_posix
        ]
        if len(candidates) > 1:
            deps.append(Dependency("skill", name, None, "ambiguous"))
            continue
        path = str(PurePosixPath(candidates[0].rel_posix).parent) if candidates else None
        deps.append(_dated(Dependency("skill", name, path, "unresolved"), history, skill_changed))
    return deps


def _dated(dep: Dependency, history: History, skill_changed: datetime | None) -> Dependency:
    if dep.path is None:
        return dep
    if history.is_unknown(dep.path):
        dep.state = "unknown"
        return dep
    changed = history.last_change(dep.path)
    dep.last_change = changed.date().isoformat() if changed else None
    if changed is not None and (skill_changed is None or changed > skill_changed):
        dep.state = "changed"
    else:
        dep.state = "unchanged"
    return dep


# --- scoring ---------------------------------------------------------------------


def score_skill(
    *,
    volatility: str,
    staleness_days: int | None,
    unknown: bool,
    churn: int,
    changed_deps: int,
    verdict: str | None,
    open_fb: int | None,
) -> dict[str, int]:
    factors: dict[str, int] = {}
    weight = VOLATILITY_WEIGHT.get(volatility, VOLATILITY_WEIGHT["medium"])
    if staleness_days:
        factors["age"] = weight * staleness_days
    if unknown:
        factors["unknown"] = UNKNOWN_POINTS
    if churn:
        factors["churn"] = CHURN_POINTS * min(churn, CHURN_CAP)
    if changed_deps:
        factors["deps"] = DEP_CHANGED_POINTS * min(changed_deps, DEP_CHANGED_CAP)
    if verdict is None:
        factors["never-dogfooded"] = NEVER_DOGFOODED_POINTS
    elif verdict == "needs-fix":
        factors["needs-fix"] = NEEDS_FIX_POINTS
    if open_fb:
        factors["fb"] = FB_POINTS * open_fb
    return factors


def explain(risk: SkillRisk) -> str:
    parts: list[str] = []
    for key, points in sorted(risk.factors.items(), key=lambda kv: -kv[1])[:3]:
        if key == "age":
            since = "baseline" if risk.last_change_state == "baseline" else "last touch"
            parts.append(f"{risk.volatility} x {risk.staleness_days}d since {since} (+{points})")
        elif key == "deps":
            names = ", ".join(risk.changed_dependencies[:3])
            parts.append(f"deps changed: {names} (+{points})")
        elif key == "churn":
            parts.append(f"{risk.churn} commits/{CHURN_WINDOW_DAYS}d (+{points})")
        elif key == "fb":
            parts.append(f"{risk.open_fb} open fb (+{points})")
        else:
            parts.append(f"{key} (+{points})")
    return "; ".join(parts)


def rank(
    root: Path = REPO_ROOT,
    *,
    today: date | None = None,
    include_deprecated: bool = False,
    history: History | None = None,
) -> tuple[list[SkillRisk], list[str]]:
    today = today or date.today()
    notes: list[str] = []
    paths = target_skill_paths(root)
    try:
        tools = load_repo_tools(root / "registry" / "repo-tools.yaml")
    except (FileNotFoundError, ValueError):
        tools = {}
        notes.append("registry/repo-tools.yaml not readable: requires_repo_tools keys unresolved")
    graph = load_graph(root, tools=tools, skill_md_paths=paths)
    history = history if history is not None else load_history(root)
    volatility_cfg = _load_yaml(root / VOLATILITY_PATH)
    ledger = _load_yaml(root / DOGFOOD_PATH).get("entries") or {}
    catalog = load_catalog_dirs(root)
    fb_root_exists = (root / FB_SKILLS_DIR).is_dir()
    if not fb_root_exists:
        notes.append(f"{FB_SKILLS_DIR} not found on this machine: open fb counted as 0")
    notes.append("open fb is terminal-local (gitignored); rankings can differ between machines")
    if history.unreadable:
        shown = ", ".join(sorted(p or "(umbrella)" for p in history.unreadable))
        notes.append(f"git history unreadable for: {shown} (affected skills shown as unknown)")

    existing_ids = {p.relative_to(root).as_posix() for p in paths}
    for key in sorted(ledger):
        if key not in existing_ids and not (root / key).is_file():
            notes.append(f"orphan ledger entry (SKILL.md missing, moved or renamed?): {key}")

    statuses: dict[str, str] = {}
    for path in paths:
        fm = read_frontmatter(path)
        meta = fm.data.get("meta") if fm else None
        status = meta.get("status") if isinstance(meta, dict) else None
        statuses[path.relative_to(root).as_posix()] = str(status) if status else "unknown"

    results: list[SkillRisk] = []
    for skill in graph.skills:
        skill_id = skill.rel_posix
        status = statuses.get(skill_id, "unknown")
        if status == "deprecated" and not include_deprecated:
            continue
        skill_dir = str(PurePosixPath(skill_id).parent)
        unknown = history.is_unknown(skill_dir)
        commits = [] if unknown else history.commits_for(skill_dir)
        changed = commits[-1].when if commits else None
        state = "unknown" if unknown else ("changed" if changed else "baseline")
        change_day = changed.date() if changed else (None if unknown else BASELINE_DATE)
        churn = sum(1 for c in commits if (today - c.when.date()).days < CHURN_WINDOW_DAYS)

        entry = ledger.get(skill_id)
        entry = entry if isinstance(entry, dict) else None
        dog_day = _as_date(entry.get("date")) if entry else None
        verdict = str(entry.get("verdict")) if entry and entry.get("verdict") else None

        touched = [d for d in (change_day, dog_day) if d is not None]
        staleness = (today - max(touched)).days if touched else None

        volatility, vol_source = resolve_volatility(skill_id, volatility_cfg)
        deps = resolve_dependencies(skill, graph, history, root, changed)
        changed_deps = [d.token for d in deps if d.state == "changed"]

        if catalog is not None and skill_dir not in catalog:
            open_fb: int | None = None
        else:
            open_fb = count_open_fb(fb_files(root, skill.name), entry) if skill.name else 0

        factors = score_skill(
            volatility=volatility,
            staleness_days=staleness,
            unknown=unknown,
            churn=churn,
            changed_deps=len(changed_deps),
            verdict=verdict,
            open_fb=open_fb,
        )
        risk = SkillRisk(
            id=skill_id,
            name=skill.name,
            status=status,
            volatility=volatility,
            volatility_source=vol_source,
            last_change=changed.date().isoformat() if changed else None,
            last_change_state=state,
            change_age_days=(today - change_day).days if change_day else None,
            churn=churn,
            dogfood_date=dog_day.isoformat() if dog_day else None,
            dogfood_verdict=verdict,
            staleness_days=staleness,
            dependencies=deps,
            changed_dependencies=changed_deps,
            open_fb=open_fb,
            score=sum(factors.values()),
            factors=factors,
            reason="",
        )
        risk.reason = explain(risk)
        results.append(risk)

    no_rule = [r.id for r in results if r.volatility_source == "no rule"]
    if no_rule:
        notes.append(f"no volatility rule ({len(no_rule)}; default used): " + ", ".join(no_rule))
    for r in results:
        for d in r.dependencies:
            if d.state in ("unresolved", "ambiguous"):
                notes.append(f"{d.state} dependency {d.kind}:{d.token} in {r.id}")

    results.sort(key=lambda r: (-r.score, r.id))
    return results, notes


# --- output ------------------------------------------------------------------------


def _change_label(r: SkillRisk) -> str:
    if r.last_change_state == "unknown":
        return "unknown"
    if r.last_change_state == "baseline":
        return f"<={BASELINE_DATE.isoformat()} ({r.change_age_days}d)"
    return f"{r.last_change} ({r.change_age_days}d)"


def format_table(results: list[SkillRisk], notes: list[str], total: int) -> str:
    header = (
        f"{'#':>3}  {'score':>5}  {'vol':<6}  {'last change':<20}  {'c30':>3}  "
        f"{'dogfood':<20}  {'deps':>4}  {'fb':>3}  {'status':<12}  skill"
    )
    lines = [header]
    for i, r in enumerate(results, 1):
        vol = r.volatility + ("*" if r.volatility_source == "no rule" else "")
        dog = f"{r.dogfood_date} {r.dogfood_verdict}" if r.dogfood_date else "never"
        fb = "n/a" if r.open_fb is None else str(r.open_fb)
        lines.append(
            f"{i:>3}  {r.score:>5}  {vol:<6}  {_change_label(r):<20}  {r.churn:>3}  "
            f"{dog:<20}  {len(r.changed_dependencies):>4}  {fb:>3}  {r.status:<12}  {r.id}"
        )
        lines.append(f"{'':>12}why: {r.reason}")
    lines.append("")
    lines.append(f"shown {len(results)} of {total} skills (c30 = substantive commits in 30 days)")
    for note in notes:
        lines.append(f"note: {note}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-risk",
        description="Rank skills by risk (staleness, volatility, changed deps, dogfooding, fb).",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--top", type=int, default=10, help="rows to show (0 = all, default 10)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument(
        "--include-deprecated", action="store_true", help="also rank meta.status: deprecated"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results, notes = rank(include_deprecated=args.include_deprecated)
    shown = results if args.top <= 0 else results[: args.top]
    if args.json:
        payload = {
            "total": len(results),
            "skills": [asdict(r) for r in shown],
            "notes": notes,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_table(shown, notes, len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
