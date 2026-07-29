"""Generate an initial draft of output/copilot-excerpt.md from vscode-docs/output/llms.txt
by asking an AI model (via the `aim` CLI) which entries are about GitHub Copilot / AI
agent features in VS Code.

check_copilot_excerpt.py and verify_agent_relevance.py both assume output/copilot-excerpt.md
already exists -- it was originally produced by hand-reviewing an LLM draft (see
README.md). This script automates producing that initial draft, e.g. for regenerating
the excerpt from scratch after a major reorganization of the upstream docs where most
of the existing curation no longer applies.

To avoid the title/description drift problem check_copilot_excerpt.py exists to catch,
this script does NOT let the AI rewrite entries. It only asks the AI to decide, per
entry, whether to include it (see prompts/prompt_generate_excerpt.md); the output
markdown is then assembled by this script itself from the original entries in
plugins/vscode/skills/vscode-docs/output/llms.txt, verbatim, grouped under their
source `## Section` headings in source order. This is the same "driver logic decides
formatting, AI only judges" split used by verify_agent_relevance.py.

The result is an UNREVIEWED DRAFT. A human must read it end-to-end and fix any
miscuration before it replaces the real output/copilot-excerpt.md -- this script
refuses to overwrite an existing file unless --force is given.

Usage: python generate_copilot_excerpt.py [--model {minimax-m3,gpt-oss-120b,glm-5.2,claude-sonnet-5}]
                                           [--source PATH] [--out PATH] [--prompt PATH] [--force]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import check_copilot_excerpt as base
import extract_uncurated_entries as eu

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_PROMPT = SKILL_DIR / "prompts" / "prompt_generate_excerpt.md"

URL_RE = re.compile(r"https?://\S+")
FETCHED_AT_RE = re.compile(r"^fetched_at:\s*(\S+)", re.MULTILINE)


def call_aim(model: str, prompt: str, source_text: str) -> str:
    full_prompt = f"{prompt}\n---\n\n{source_text}"
    result = subprocess.run(
        ["aim", "--model", model],
        input=full_prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"aim CLI failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def extract_urls(ai_output: str) -> set[str]:
    urls = set()
    for match in URL_RE.finditer(ai_output):
        urls.add(match.group(0).rstrip(").,:;\"'>"))
    return urls


def build_excerpt(
    entries: list[dict], included_urls: set[str], source_rel: str, fetched_at: str, model: str
) -> tuple[str, int]:
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "---",
        f"source: {source_rel}",
        f"extracted_from_fetched_at: {fetched_at}",
        f"generated_at: {generated_at}",
        f"generated_by: generate_copilot_excerpt.py (aim --model {model})",
        "note: >",
        "  DRAFT generated automatically by asking an AI model which entries in",
        "  vscode-docs/output/llms.txt relate to GitHub Copilot / AI features in VS",
        "  Code. This has NOT been reviewed by a human yet -- treat it as a starting",
        "  point, not a replacement for the curated output/copilot-excerpt.md. Review",
        "  every entry, then run check_copilot_excerpt.py to confirm titles/URLs match,",
        "  before using it to replace the real file.",
        "---",
        "",
    ]
    current_section = None
    included_count = 0
    for entry in entries:
        if entry["url"] not in included_urls:
            continue
        if entry["section"] != current_section:
            if current_section is not None:
                lines.append("")
            lines.append(f"## {entry['section']}")
            lines.append("")
            current_section = entry["section"]
        lines.append(f"- [{entry['title']}]({entry['url']}): {entry['desc']}")
        included_count += 1
    return "\n".join(lines) + "\n", included_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="minimax-m3",
        choices=["minimax-m3", "gpt-oss-120b", "glm-5.2", "claude-sonnet-5"],
    )
    parser.add_argument("--source", type=Path, default=base.DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=base.DEFAULT_EXCERPT)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--force", action="store_true", help="overwrite --out if it already exists")
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"ERROR: source file not found: {args.source}", file=sys.stderr)
        print("Run the vscode-docs skill's download script first.", file=sys.stderr)
        return 2
    if args.out.exists() and not args.force:
        print(
            f"ERROR: {args.out} already exists. Pass --force to overwrite, or --out "
            "to write a draft elsewhere for review (recommended).",
            file=sys.stderr,
        )
        return 2
    if not args.prompt.is_file():
        print(f"ERROR: prompt file not found: {args.prompt}", file=sys.stderr)
        return 2

    source_text = args.source.read_text(encoding="utf-8")
    fetched_at_match = FETCHED_AT_RE.search(source_text)
    fetched_at = fetched_at_match.group(1) if fetched_at_match else "(unknown)"

    entries = eu.parse_entries_with_section(source_text)
    if not entries:
        print(f"ERROR: no entries parsed from source file: {args.source}", file=sys.stderr)
        return 2

    prompt = args.prompt.read_text(encoding="utf-8")
    print(f"Calling aim --model {args.model} to judge {len(entries)} source entries ...")
    try:
        ai_output = call_aim(args.model, prompt, source_text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    source_urls = {e["url"] for e in entries}
    ai_urls = extract_urls(ai_output)
    included_urls = ai_urls & source_urls
    unknown_urls = ai_urls - source_urls
    if unknown_urls:
        print(
            f"WARNING: ignoring {len(unknown_urls)} URL(s) from AI output not present "
            "in source (hallucinated or mistyped):",
            file=sys.stderr,
        )
        for url in sorted(unknown_urls):
            print(f"  - {url}", file=sys.stderr)

    if not included_urls:
        print(
            "ERROR: AI output contained no URLs matching the source. Aborting without "
            "writing output.",
            file=sys.stderr,
        )
        return 2

    source_rel = Path(os.path.relpath(args.source.resolve(), args.out.resolve().parent)).as_posix()

    excerpt_text, included_count = build_excerpt(
        entries, included_urls, source_rel, fetched_at, args.model
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(excerpt_text, encoding="utf-8")

    print(f"Included {included_count}/{len(entries)} source entries -> {args.out}")
    print(
        "\nThis is an UNREVIEWED DRAFT. A human must read it end-to-end, fix any "
        "mis-curated entries, then run check_copilot_excerpt.py to confirm titles/URLs "
        "match before treating it as the real output/copilot-excerpt.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
