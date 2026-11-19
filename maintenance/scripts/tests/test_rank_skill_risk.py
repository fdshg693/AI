from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill.query import rank_skill_risk as rsr  # noqa: E402

TODAY = date(2026, 11, 20)


def git(cwd: Path, *args: str, env_date: str | None = None) -> None:
    env = None
    if env_date:
        import os

        env = {**os.environ, "GIT_AUTHOR_DATE": env_date, "GIT_COMMITTER_DATE": env_date}
    subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env=env,
    )


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "test")
    git(path, "config", "commit.gpgsign", "false")
    git(path, "config", "core.hooksPath", "/dev/null")


def commit(repo: Path, message: str, when: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message, env_date=when)


def write_skill(root: Path, rel_dir: str, name: str, meta: str = "") -> None:
    folder = root / rel_dir
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: d\nmeta:\n  status: stable\n{meta}---\nbody\n",
        encoding="utf-8",
    )


def write_inputs(root: Path, ledger: dict | None = None) -> None:
    (root / "maintenance/skill-risk").mkdir(parents=True, exist_ok=True)
    (root / rsr.VOLATILITY_PATH).write_text(
        "default: medium\n"
        "rules:\n"
        "  - prefix: skills/plugins/\n    level: low\n"
        "  - prefix: skills/plugins/know/\n    level: high\n"
        "overrides:\n"
        "  skills/plugins/know/skills/special/SKILL.md:\n    level: low\n",
        encoding="utf-8",
    )
    (root / rsr.DOGFOOD_PATH).write_text(
        "entries: " + json.dumps(ledger or {}) + "\n", encoding="utf-8"
    )
    (root / "registry").mkdir(exist_ok=True)
    (root / "registry/repo-tools.yaml").write_text(
        "tools:\n  mytool:\n    path: tools/mytool\n", encoding="utf-8"
    )


def by_id(results: list[rsr.SkillRisk]) -> dict[str, rsr.SkillRisk]:
    return {r.id: r for r in results}


def test_volatility_resolution_order() -> None:
    cfg = {
        "default": "medium",
        "rules": [
            {"prefix": "a/", "level": "low"},
            {"prefix": "a/b/", "level": "high"},
        ],
        "overrides": {"a/b/x/SKILL.md": {"level": "low"}},
    }
    assert rsr.resolve_volatility("a/b/x/SKILL.md", cfg) == ("low", "override")
    assert rsr.resolve_volatility("a/b/y/SKILL.md", cfg) == ("high", "rule")
    assert rsr.resolve_volatility("a/c/SKILL.md", cfg) == ("low", "rule")
    assert rsr.resolve_volatility("z/SKILL.md", cfg) == ("medium", "no rule")


def test_bulk_commit_rule() -> None:
    assert rsr.is_bulk_commit("refactor(repo): move things", 3)
    assert rsr.is_bulk_commit("chore(repo): import existing tree", 3)
    assert rsr.is_bulk_commit("refactor(tools): regroup", rsr.BULK_FILE_LIMIT + 1)
    assert not rsr.is_bulk_commit("docs(skills): sync", rsr.BULK_FILE_LIMIT)


def test_score_formula() -> None:
    factors = rsr.score_skill(
        volatility="high",
        staleness_days=4,
        unknown=False,
        churn=9,
        changed_deps=5,
        verdict=None,
        open_fb=2,
    )
    assert factors == {
        "age": 3 * 4,
        "churn": rsr.CHURN_POINTS * rsr.CHURN_CAP,
        "deps": rsr.DEP_CHANGED_POINTS * rsr.DEP_CHANGED_CAP,
        "never-dogfooded": rsr.NEVER_DOGFOODED_POINTS,
        "fb": 2 * rsr.FB_POINTS,
    }
    ok = rsr.score_skill(
        volatility="low",
        staleness_days=0,
        unknown=False,
        churn=0,
        changed_deps=0,
        verdict="ok",
        open_fb=None,
    )
    assert ok == {}


def test_count_open_fb() -> None:
    files = ["20261115-100000-fb.md", "20261118-090000-fb.md", "20261118-120000-fb.md"]
    assert rsr.count_open_fb(files, None) == 3
    assert rsr.count_open_fb(files, {"date": "2026-11-17"}) == 2
    assert rsr.count_open_fb(files, {"date": "2026-11-18", "fb": "20261118-090000-fb.md"}) == 1


def test_rank_end_to_end_with_submodule(tmp_path: Path) -> None:
    upstream = tmp_path / "upstream"
    init_repo(upstream)
    write_skill(upstream, "plugins/know/skills/alpha", "alpha", "  requires_skills: beta\n")
    write_skill(upstream, "plugins/know/skills/beta", "beta")
    write_skill(upstream, "plugins/know/skills/special", "special")
    write_skill(upstream, "plugins/know/skills/special/sub_skills/part", "part")
    write_skill(upstream, "plugins/coding/skills/gamma", "gamma", "  requires_repo_tools: mytool\n")
    commit(upstream, "refactor(repo): move skills", "2026-11-10T12:00:00+09:00")
    (upstream / "plugins/know/skills/alpha/note.md").write_text("x\n", encoding="utf-8")
    commit(upstream, "docs(skills): touch alpha", "2026-11-12T12:00:00+09:00")
    (upstream / "plugins/know/skills/beta/note.md").write_text("x\n", encoding="utf-8")
    commit(upstream, "docs(skills): touch beta", "2026-11-15T12:00:00+09:00")

    root = tmp_path / "umbrella"
    init_repo(root)
    git(root, "submodule", "add", "-q", str(upstream), "skills")
    write_inputs(
        root,
        ledger={
            "skills/plugins/know/skills/special/SKILL.md": {"date": "2026-11-19", "verdict": "ok"},
            "skills/plugins/gone/SKILL.md": {"date": "2026-11-19", "verdict": "ok"},
        },
    )
    (root / "tools/mytool").mkdir(parents=True)
    (root / "tools/mytool/main.py").write_text("print()\n", encoding="utf-8")
    (root / "temp/skills/alpha").mkdir(parents=True)
    (root / "temp/skills/alpha/SKILL.md").write_text("---\nname: alpha\n---\n", encoding="utf-8")
    commit(root, "chore: init", "2026-11-11T12:00:00+09:00")
    (root / "tools/mytool/main.py").write_text("print(1)\n", encoding="utf-8")
    commit(root, "feat(tools): change mytool", "2026-11-16T12:00:00+09:00")

    results, notes = rsr.rank(root, today=TODAY)
    found = by_id(results)

    # Scope: only plugin roots, nested part and temp/ copy excluded.
    assert sorted(found) == [
        "skills/plugins/coding/skills/gamma/SKILL.md",
        "skills/plugins/know/skills/alpha/SKILL.md",
        "skills/plugins/know/skills/beta/SKILL.md",
        "skills/plugins/know/skills/special/SKILL.md",
    ]

    alpha = found["skills/plugins/know/skills/alpha/SKILL.md"]
    assert alpha.last_change == "2026-11-12"
    assert alpha.last_change_state == "changed"
    assert alpha.churn == 1
    assert alpha.volatility == "high"
    assert alpha.changed_dependencies == ["beta"]  # beta changed after alpha
    assert alpha.open_fb == 0  # no catalog file -> fb eligible, no fb dir -> 0

    beta = found["skills/plugins/know/skills/beta/SKILL.md"]
    assert beta.changed_dependencies == []

    gamma = found["skills/plugins/coding/skills/gamma/SKILL.md"]
    assert gamma.last_change_state == "baseline"  # only the bulk move touched it
    assert gamma.change_age_days == (TODAY - rsr.BASELINE_DATE).days
    assert gamma.volatility == "low"
    assert gamma.changed_dependencies == ["mytool"]

    special = found["skills/plugins/know/skills/special/SKILL.md"]
    assert special.volatility_source == "override"
    assert special.dogfood_verdict == "ok"
    assert special.staleness_days == 1  # dogfooded yesterday beats baseline age
    assert "never-dogfooded" not in special.factors

    assert results[-1].id == special.id
    assert any("orphan ledger entry" in n and "gone" in n for n in notes)
    assert any(rsr.FB_SKILLS_DIR in n for n in notes)


def test_unknown_history_and_catalog_and_deprecated(tmp_path: Path) -> None:
    root = tmp_path / "umbrella"
    write_skill(root, "maintenance/plugin/skills/m", "m", "  requires_repo_tools: missing/file\n")
    write_skill(root, "tools/_plugin/x/skills/t", "t")
    write_skill(root, "tools/_plugin/x/skills/old", "old")
    old = root / "tools/_plugin/x/skills/old/SKILL.md"
    old.write_text(old.read_text(encoding="utf-8").replace("stable", "deprecated"), "utf-8")
    write_inputs(root)
    (root / ".claude-plugin").mkdir()
    (root / rsr.CATALOG_PATH).write_text(
        json.dumps({"tools/_plugin/x": [{"path": "tools/_plugin/x/skills/t", "name": "t"}]}),
        encoding="utf-8",
    )
    fb_dir = root / rsr.FB_SKILLS_DIR / "t"
    fb_dir.mkdir(parents=True)
    (fb_dir / "20261118-100000-fb.md").write_text("fb\n", encoding="utf-8")

    history = rsr.History(unreadable={"tools"}, readable={""})
    results, notes = rsr.rank(root, today=TODAY, history=history)
    found = by_id(results)

    assert "tools/_plugin/x/skills/old/SKILL.md" not in found
    t = found["tools/_plugin/x/skills/t/SKILL.md"]
    assert t.last_change_state == "unknown"
    assert t.factors["unknown"] == rsr.UNKNOWN_POINTS
    assert t.open_fb == 1
    assert results[0].id == t.id

    m = found["maintenance/plugin/skills/m/SKILL.md"]
    assert m.open_fb is None  # not in the catalog
    assert m.dependencies[0].state == "unresolved"
    assert any("unresolved dependency repo_tool:missing/file" in n for n in notes)
    assert any("unreadable" in n for n in notes)

    with_old, _ = rsr.rank(root, today=TODAY, history=history, include_deprecated=True)
    assert "tools/_plugin/x/skills/old/SKILL.md" in by_id(with_old)
