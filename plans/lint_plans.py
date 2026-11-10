#!/usr/bin/env python3
"""Lint plan folders: frontmatter values, dependencies, and checkbox consistency.

Usage:
    uv run plans/lint_plans.py plans
    python plans/lint_plans.py plans [--strict]
    uv run plans/lint_plans.py --examples plans/references

Checks (plan = `{plan-name}/00-overview.md` or a single-file plan `{plan-name}.md`):
    - frontmatter exists; `type` is Plan / Plan Step; `status` is one of the 6 values
    - `order` is `N/M` with 1 <= N <= M; required when depends_on/blocks exist
    - depends_on / blocks: target exists, no self reference, mutual pairing, no cycles
    - overview checkboxes (`- [x]`) agree with the linked step file `status` (done <=> checked)
    - required `##` sections per file kind once status is ready or later
      (REQUIRED_SECTIONS; the source of truth is the "節構成" table in
      guides/plan-writing.md -- keep both in sync)
    - folder plans with status implementing-* have snapshot/
    - implementing-done plans have a completion record (folder: progress/99-*.md or a
      progress file with `## 完了記録`; single file: its own `## 完了記録` section)
    - rough/ files: type Rough Plan, status in the 4 rough values

Problems are printed as `path:line: message`.
Exit code 1 if any error. `--strict` also fails on warnings.

`--examples` lints the template samples (`references/`, laid out like `plans/`):
references to (fictional) sibling plans that do not exist are only warnings, and the
snapshot/ check is skipped because the samples do not include a snapshot.

Only the standard library is used.
"""

import argparse
import re
import sys
from pathlib import Path

PLAN_STATUSES = {
    "planning-research",
    "planning-breakdown",
    "ready",
    "implementing-started",
    "implementing-in-progress",
    "implementing-done",
}
ROUGH_STATUSES = {"drafting", "ready-for-plan", "promoted", "abandoned"}
SKIP_DIRS = {"guides", "references", "snapshot", "progress", "rough"}
# Required `##` headings, matched by prefix. Source of truth: guides/plan-writing.md「節構成」.
IMPLEMENTATION_SECTIONS = ("やること", "読むべきファイル", "触るファイル", "決定事項", "ルール更新ポイント", "進め方")
REQUIRED_SECTIONS = {
    "overview": ("実装ステータス", "要件", "実装ステップ", "主要な決定事項", "変更/新規ファイル一覧", "ルール更新ポイント", "進め方"),
    "implementation": IMPLEMENTATION_SECTIONS,
    "research": ("やること", "調査観点", "調査結果", "進め方"),
    "single": IMPLEMENTATION_SECTIONS,
}
RESEARCH_MARKER = "調査観点"
COMPLETION_SECTION = "完了記録"
HEADING = re.compile(r"^##\s+(.+?)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
SKIP_FILES = {"readme.md", "agents.md", "claude.md"}
CHECKBOX = re.compile(r"^\s*- \[([ xX])\]\s*(.*)$")
LINK_TARGET = re.compile(r"\]\(([^)#\s]+)")


class Frontmatter(dict):
    """Frontmatter values plus the file line number of each key / list item."""

    def __init__(self):
        super().__init__()
        self.lines = {}

    def line(self, key):
        return self.lines.get(key, 1)


def parse_frontmatter(text):
    """Minimal parser: scalars and `key:` followed by `- item` lists. Comments stripped."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match:
        return None
    fm, current = Frontmatter(), None
    for lineno, raw in enumerate(match.group(1).splitlines(), start=2):
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s+(.+)$", line)
        if item and current is not None:
            if not isinstance(fm.get(current), list):
                fm[current] = []
            fm.lines[f"{current}[{len(fm[current])}]"] = lineno
            fm[current].append(item.group(1).strip())
            continue
        kv = re.match(r"^([\w-]+):\s*(.*)$", line)
        if kv:
            current = kv.group(1)
            fm[current] = kv.group(2).strip() if kv.group(2).strip() else []
            fm.lines[current] = lineno
    return fm


def as_list(value):
    if isinstance(value, list):
        return value
    return [value] if value else []


class Linter:
    def __init__(self, examples=False):
        self.examples = examples
        self.errors = []
        self.warnings = []

    @staticmethod
    def _format(path, line, msg):
        return f"{path}:{line}: {msg}" if line else f"{path}: {msg}"

    def error(self, path, msg, line=None):
        self.errors.append(self._format(path, line, msg))

    def warn(self, path, msg, line=None):
        self.warnings.append(self._format(path, line, msg))

    def load(self, path):
        if not path.is_file():
            self.error(path, "ファイルが無い")
            return None
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            self.error(path, "frontmatter が無い", 1)
        return fm

    def lint_plan_file(self, path, expected_type):
        fm = self.load(path)
        if fm is None:
            return None
        if fm.get("type") != expected_type:
            self.error(path, f"type は '{expected_type}' であるべき（現在: {fm.get('type')!r}）", fm.line("type"))
        if fm.get("status") not in PLAN_STATUSES:
            self.error(path, f"status が不正: {fm.get('status')!r}", fm.line("status"))
        if expected_type == "Plan Step":
            for key in ("order", "depends_on", "blocks"):
                if key in fm:
                    self.error(path, f"Plan Step に `{key}` は書かない（overview のみ）", fm.line(key))
        return fm

    def lint_rough(self, path):
        fm = self.load(path)
        if fm is None:
            return
        if fm.get("type") != "Rough Plan":
            self.error(path, f"type は 'Rough Plan' であるべき（現在: {fm.get('type')!r}）", fm.line("type"))
        if fm.get("status") not in ROUGH_STATUSES:
            self.error(path, f"rough の status が不正: {fm.get('status')!r}", fm.line("status"))

    @staticmethod
    def checkboxes(path):
        """Yield (line number, checked, label, linked file name or None) for each checkbox."""
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            box = CHECKBOX.match(line)
            if not box:
                continue
            label = box.group(2)
            link = LINK_TARGET.search(label)
            yield lineno, box.group(1).lower() == "x", label, Path(link.group(1)).name if link else None

    def lint_checkboxes(self, overview, step_fms):
        """step_fms: {step file name: frontmatter}"""
        for lineno, checked, label, target in self.checkboxes(overview):
            name = target
            if name is None:
                # Unlinked label such as `01-research.md — ...`: match by the step number prefix.
                num = re.match(r"\s*`?(\d{2})-", label)
                name = next((n for n in step_fms if num and n.startswith(num.group(1) + "-")), None)
            fm = step_fms.get(name)
            if fm is None:
                continue
            done = fm.get("status") == "implementing-done"
            if done != checked:
                self.error(
                    overview,
                    f"チェックボックス（{name}）と {name} の status ({fm.get('status')}) が不一致",
                    lineno,
                )

    @staticmethod
    def headings(path):
        """Return [(line number, title)] of `## ` headings outside fenced code blocks."""
        found, fenced = [], False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if FENCE.match(line):
                fenced = not fenced
                continue
            heading = None if fenced else HEADING.match(line)
            if heading:
                found.append((lineno, heading.group(1)))
        return found

    def lint_sections(self, path, fm, kind, extra=()):
        if fm.get("status", "").startswith("planning-"):
            return  # sections are filled while planning; required from `ready` on
        titles = [title for _, title in self.headings(path)]
        for name in (*REQUIRED_SECTIONS[kind], *extra):
            if not any(title.startswith(name) for title in titles):
                self.error(path, f"必須の節 `## {name}` が無い（guides/plan-writing.md「節構成」）")
        if kind == "overview" and titles and not titles[0].startswith("実装ステータス"):
            self.error(path, "`## 実装ステータス` は frontmatter 直後の最初の節に置く")

    def lint_step_sections(self, path, fm):
        titles = [title for _, title in self.headings(path)]
        research = any(title.startswith(RESEARCH_MARKER) for title in titles)
        self.lint_sections(path, fm, "research" if research else "implementation")

    def has_completion_record(self, progress_dir):
        if not progress_dir.is_dir():
            return False
        if any(progress_dir.glob("99-*.md")):
            return True
        return any(
            title.startswith(COMPLETION_SECTION)
            for path in progress_dir.glob("*.md")
            for _, title in self.headings(path)
        )

    @staticmethod
    def step_files(folder):
        return [p for p in sorted(folder.glob("[0-9][0-9]-*.md")) if not p.name.startswith("00-")]

    def lint_folder_plan(self, folder, overview):
        fm = self.lint_plan_file(overview, "Plan")
        steps = self.step_files(folder)
        step_fms = {}
        for step in steps:
            step_fm = self.lint_plan_file(step, "Plan Step")
            if step_fm:
                step_fms[step.name] = step_fm
                self.lint_step_sections(step, step_fm)
        if fm:
            self.lint_sections(overview, fm, "overview")
            self.lint_checkboxes(overview, step_fms)
            status = fm.get("status", "")
            if status.startswith("implementing-") and not self.examples and not (folder / "snapshot").is_dir():
                self.error(overview, "実行着手後（implementing-*）だが snapshot/ が無い", fm.line("status"))
            if status == "implementing-done":
                if any(s.get("status") != "implementing-done" for s in step_fms.values()):
                    self.error(overview, "overview が implementing-done だが未完了のステップがある", fm.line("status"))
                if not self.has_completion_record(folder / "progress"):
                    self.error(
                        overview,
                        f"implementing-done だが完了記録が無い（progress/99-*.md か progress の `## {COMPLETION_SECTION}` 節）",
                        fm.line("status"),
                    )
        rough_dir = folder / "rough"
        if rough_dir.is_dir():
            for rough in sorted(rough_dir.glob("*.md")):
                self.lint_rough(rough)
        return fm, steps

    def lint_dependencies(self, plans):
        """plans: {resolved plan file path: frontmatter}"""
        graph = {}
        for path, fm in plans.items():
            deps = as_list(fm.get("depends_on"))
            blocks = as_list(fm.get("blocks"))
            order = str(fm.get("order", ""))
            if (deps or blocks) and not re.match(r"^\d+/\d+$", order):
                self.error(path, "依存関係があるプランには `order: N/M` が必須", fm.line("order") if order else 1)
            elif order:
                if not re.match(r"^\d+/\d+$", order):
                    self.error(path, f"order の書式が不正: {order}", fm.line("order"))
                else:
                    cur, total = map(int, order.split("/"))
                    if not 1 <= cur <= total:
                        self.error(path, f"order が範囲外: {order}", fm.line("order"))
            for key, items in (("depends_on", deps), ("blocks", blocks)):
                back_key = "blocks" if key == "depends_on" else "depends_on"
                for i, item in enumerate(items):
                    line = fm.line(f"{key}[{i}]")
                    target = (path.parent / item).resolve()
                    if target == path:
                        self.error(path, f"{key} が自己参照", line)
                    elif target not in plans:
                        report = self.warn if self.examples and not target.exists() else self.error
                        report(path, f"{key} の参照先が見つからない/lint対象外: {item}", line)
                    else:
                        back = [(target.parent / b).resolve() for b in as_list(plans[target].get(back_key))]
                        if path not in back:
                            self.error(path, f"{key} {item} に対応する {back_key} が相手側に無い（片側宣言）", line)
            graph[path] = {(path.parent / d).resolve() for d in deps}

        visiting, done = set(), set()

        def visit(node, trail):
            if node in done:
                return
            if node in visiting:
                cycle = " -> ".join(p.parent.name for p in trail + [node])
                self.error(node, "depends_on が循環: " + cycle, plans[node].line("depends_on"))
                return
            visiting.add(node)
            for nxt in graph.get(node, ()):
                if nxt in graph:
                    visit(nxt, trail + [node])
            visiting.discard(node)
            done.add(node)

        for node in graph:
            visit(node, [])

    def lint_single_plan(self, path):
        fm = self.lint_plan_file(path, "Plan")
        if fm:
            done = fm.get("status") == "implementing-done"
            self.lint_sections(path, fm, "single", (COMPLETION_SECTION,) if done else ())
        return fm

    def run(self, root):
        plans = {}
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                overview = entry / "00-overview.md"
                if entry.name in SKIP_DIRS or not overview.is_file():
                    continue
                fm, _ = self.lint_folder_plan(entry, overview)
                if fm:
                    plans[overview.resolve()] = fm
            elif entry.suffix == ".md" and entry.name.lower() not in SKIP_FILES:
                fm = self.lint_single_plan(entry)
                if fm:
                    plans[entry.resolve()] = fm
        self.lint_dependencies(plans)
        return len(plans)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plans_dir", type=Path, help="プランを置くルート（例: plans）")
    parser.add_argument("--strict", action="store_true", help="警告でも失敗扱いにする")
    parser.add_argument("--examples", action="store_true", help="テンプレートのサンプル（references/）を検査する")
    args = parser.parse_args()
    if not args.plans_dir.is_dir():
        print(f"error: not a directory: {args.plans_dir}", file=sys.stderr)
        return 1
    linter = Linter(examples=args.examples)
    count = linter.run(args.plans_dir)
    for line in linter.warnings:
        print(f"warn : {line}")
    for line in linter.errors:
        print(f"error: {line}")
    print(f"checked {count} plan(s): {len(linter.errors)} error(s), {len(linter.warnings)} warning(s)")
    return 1 if linter.errors or (args.strict and linter.warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
