"""Run one dogfooding scenario in an isolated `claude -p` and print a short report.

The main agent should not read the raw stream-json (it gets large). This script
runs the scenario, saves the raw stream to ``<workdir>/stream.jsonl`` and prints
only what the dogfooding cycle needs:

- whether a skill was invoked through the Skill tool (and which one)
- tool use counts, Bash commands, tool errors and permission denials
- the final answer (which ends with the scenario report, see REPORT_TRAILER)
- turns and cost

Safety model (decided in plans/skill-risk-dogfooding Step4):

- ``--setting-sources ""``: no user/project settings, hooks or other plugins;
  only the target plugin from ``--plugin-dir`` is loaded. ``--strict-mcp-config``
  also keeps account-level MCP connectors out.
- ``--permission-mode dontAsk``: any tool call not in the allow list is denied
  without a prompt (and shows up under "permission denials").
- the allow list is read-only by default (READ_ONLY_ALLOW); a scenario adds the
  exact Bash patterns it needs with ``--allow``.
- ``--disallowedTools`` (EXTERNAL_WRITE_DENY) blocks external writes even when a
  broad ``--allow`` pattern would match them. Deny wins over allow.
- the session runs in a scratch working directory and is not persisted.

Stdlib only. Usage: ``python run_dogfood.py --help``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

READ_ONLY_ALLOW = [
    "Read",
    "Glob",
    "Grep",
    "Skill",
    "WebFetch",
    "WebSearch",
    "TodoWrite",
    "Bash(git status:*)",
    "Bash(git log:*)",
    "Bash(git diff:*)",
    "Bash(git show:*)",
    "Bash(ls:*)",
    "Bash(cat:*)",
    "Bash(head:*)",
    "Bash(rg:*)",
]

EXTERNAL_WRITE_DENY = [
    "Bash(git push:*)",
    "Bash(git commit:*)",
    "Bash(git reset:*)",
    "Bash(git checkout:*)",
    "Bash(git switch:*)",
    "Bash(gh pr create:*)",
    "Bash(gh pr merge:*)",
    "Bash(gh pr close:*)",
    "Bash(gh pr comment:*)",
    "Bash(gh pr edit:*)",
    "Bash(gh pr review:*)",
    "Bash(gh issue create:*)",
    "Bash(gh issue close:*)",
    "Bash(gh issue comment:*)",
    "Bash(gh issue edit:*)",
    "Bash(gh release:*)",
    "Bash(gh workflow run:*)",
    "Bash(gh run rerun:*)",
    "Bash(gh secret:*)",
    "Bash(gh api:*)",
    "Bash(az:*)",
    "Bash(azd:*)",
    "Bash(aws:*)",
    "Bash(gcloud:*)",
    "Bash(terraform apply:*)",
    "Bash(terraform destroy:*)",
    "Bash(npm publish:*)",
    "Bash(pnpm publish:*)",
    "Bash(uv publish:*)",
    "Bash(rm -rf:*)",
]

REPORT_TRAILER = """

---
作業を終えたら、最後に次の 4 点を短く報告してください（改善案は書かない）。
1. 使ったスキル・ドキュメント・コマンド
2. 手順どおりに最後まで進められたか（進められなかったなら、どこで止まったか）
3. 実在しなかった・古かった・説明と違ったコマンド、パス、仕様
4. 迷った・遠回りした箇所
外部への書き込み（push、PR、Issue、コメント、クラウドの操作、パッケージの公開）は行わず、必要になったら「ここで書き込みが必要」と書いてそこで止めてください。
"""

TEXT_LIMIT = 300


def _short(text: str, limit: int = TEXT_LIMIT) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def plugin_name(plugin_dir: Path) -> str | None:
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("name")
    except (OSError, ValueError):
        return None


def build_command(args: argparse.Namespace, claude: str) -> list[str]:
    allow = READ_ONLY_ALLOW + list(args.allow)
    cmd = [
        claude,
        "-p",
        "--plugin-dir",
        str(args.plugin_dir),
        "--setting-sources",
        "",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "dontAsk",
        "--model",
        args.model,
        "--max-turns",
        str(args.max_turns),
        "--max-budget-usd",
        str(args.max_budget_usd),
        "--allowedTools",
        ",".join(allow),
        "--disallowedTools",
        ",".join(EXTERNAL_WRITE_DENY),
    ]
    for extra in args.add_dir:
        cmd += ["--add-dir", str(extra)]
    return cmd


def _tool_result_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"
        )
    return str(content)


def summarize(lines: list[str], expect_skill: str | None, prefix: str | None) -> dict[str, Any]:
    tools: Counter[str] = Counter()
    skills: list[str] = []
    bash: list[str] = []
    errors: list[str] = []
    loaded: list[str] = []
    plugin_errors: list[str] = []
    result: dict[str, Any] = {}
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        kind = ev.get("type")
        if kind == "system" and ev.get("subtype") == "init":
            names = ev.get("skills") or []
            loaded = [n for n in names if not prefix or str(n).startswith(prefix + ":")]
            plugin_errors = [
                _short(str(e.get("message") or e)) for e in ev.get("plugin_errors") or []
            ]
        elif kind == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name", "?")
                tools[name] += 1
                inp = block.get("input") or {}
                if name == "Skill":
                    skills.append(str(inp.get("skill") or inp.get("command") or inp))
                elif name in ("Bash", "PowerShell"):
                    bash.append(_short(str(inp.get("command", "")), 200))
        elif kind == "user":
            for block in (ev.get("message") or {}).get("content") or []:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_result"
                    and block.get("is_error")
                ):
                    errors.append(_short(_tool_result_text(block.get("content"))))
        elif kind == "result":
            result = ev
    invoked = None
    if expect_skill:
        invoked = any(
            s == expect_skill or s.split(":")[-1] == expect_skill.split(":")[-1] for s in skills
        )
    denials = [
        f"{d.get('tool_name')}: {_short(json.dumps(d.get('tool_input'), ensure_ascii=False), 200)}"
        for d in result.get("permission_denials") or []
    ]
    return {
        "loaded_plugin_skills": len(loaded),
        "plugin_errors": plugin_errors,
        "skill_invocations": skills,
        "expected_skill": expect_skill,
        "expected_skill_invoked": invoked,
        "tool_uses": dict(tools.most_common()),
        "bash_commands": bash,
        "tool_errors": errors,
        "permission_denials": denials,
        "subtype": result.get("subtype"),
        "is_error": result.get("is_error"),
        "num_turns": result.get("num_turns"),
        "cost_usd": result.get("total_cost_usd"),
        "final": result.get("result", ""),
    }


def print_report(report: dict[str, Any], raw_path: Path) -> None:
    exp = report["expected_skill"]
    print(f"raw stream: {raw_path}")
    print(
        f"result: {report['subtype']} (error={report['is_error']}) turns={report['num_turns']} cost=${report['cost_usd']}"
    )
    print(f"plugin skills loaded: {report['loaded_plugin_skills']}")
    for err in report["plugin_errors"]:
        print(f"  plugin error: {err}")
    print(f"skill invocations: {', '.join(report['skill_invocations']) or '(none)'}")
    if exp:
        print(
            f"expected skill {exp}: {'INVOKED' if report['expected_skill_invoked'] else 'NOT INVOKED'}"
        )
    print(
        "tool uses: " + (", ".join(f"{k}={v}" for k, v in report["tool_uses"].items()) or "(none)")
    )
    for title, key in (
        ("bash", "bash_commands"),
        ("tool errors", "tool_errors"),
        ("permission denials", "permission_denials"),
    ):
        items = report[key]
        print(f"{title}: {len(items)}")
        for item in items:
            print(f"  - {item}")
    print("--- final answer ---")
    print(report["final"])


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="run_dogfood",
        description="Run one dogfooding scenario in an isolated claude -p and print a short report.",
    )
    p.add_argument(
        "--plugin-dir",
        required=True,
        type=Path,
        help="target plugin directory (has .claude-plugin/plugin.json)",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt", help="scenario request text")
    src.add_argument("--prompt-file", type=Path, help="file holding the scenario request (UTF-8)")
    p.add_argument(
        "--expect-skill",
        help="skill name the scenario should invoke (e.g. topics:linear-docs or linear-docs)",
    )
    p.add_argument("--workdir", type=Path, help="scratch working directory (default: new temp dir)")
    p.add_argument(
        "--add-dir",
        action="append",
        default=[],
        type=Path,
        help="extra readable directory (repeatable)",
    )
    p.add_argument(
        "--allow",
        action="append",
        default=[],
        help='extra allowed tool rule, e.g. "Bash(just --justfile maintenance/scripts/justfile skill-risk:*)" (repeatable)',
    )
    p.add_argument(
        "--model",
        default="sonnet",
        help="model alias (default: sonnet; haiku for invocation-only checks)",
    )
    p.add_argument("--max-turns", type=int, default=30)
    p.add_argument("--max-budget-usd", type=float, default=1.0)
    p.add_argument(
        "--no-report-trailer", action="store_true", help="do not append the 4-point report request"
    )
    p.add_argument("--json", action="store_true", help="print the summary as JSON")
    p.add_argument("--dry-run", action="store_true", help="print the claude command and exit")
    args = p.parse_args(argv)

    args.plugin_dir = args.plugin_dir.resolve()
    if not (args.plugin_dir / ".claude-plugin" / "plugin.json").is_file():
        print(f"error: no .claude-plugin/plugin.json under {args.plugin_dir}", file=sys.stderr)
        return 2
    prompt = (
        args.prompt if args.prompt is not None else args.prompt_file.read_text(encoding="utf-8")
    )
    if not args.no_report_trailer:
        prompt += REPORT_TRAILER

    claude = shutil.which("claude")
    if not claude:
        print("error: claude CLI not found on PATH", file=sys.stderr)
        return 2
    workdir = (args.workdir or Path(tempfile.mkdtemp(prefix="dogfood-"))).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = build_command(args, claude)
    if args.dry_run:
        print(" ".join(json.dumps(c) if (" " in c or not c) else c for c in cmd))
        print(f"cwd: {workdir}")
        return 0

    proc = subprocess.run(
        cmd,
        input=prompt,
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw_path = workdir / "stream.jsonl"
    raw_path.write_text(proc.stdout, encoding="utf-8")
    lines = proc.stdout.splitlines()
    report = summarize(lines, args.expect_skill, plugin_name(args.plugin_dir))
    if proc.returncode != 0 and not report["subtype"]:
        print(f"error: claude exited {proc.returncode}", file=sys.stderr)
        print(_short(proc.stderr, 2000), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"raw_stream": str(raw_path), **report}, ensure_ascii=False, indent=2))
    else:
        print_report(report, raw_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
