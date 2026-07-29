"""markdown / json 整形。"""

from __future__ import annotations

import json
from typing import TypedDict


class SummaryEntry(TypedDict):
    file_path: str
    summary: str | None
    model: str | None
    generated_at: str | None
    content_hash: str | None


def format_markdown(entries: list[SummaryEntry]) -> str:
    blocks = []
    for entry in entries:
        body = entry["summary"] if entry["summary"] is not None else "(要約未生成)"
        blocks.append(f"## {entry['file_path']}\n\n{body}\n")
    return "\n".join(blocks)


def format_json(entries: list[SummaryEntry]) -> str:
    return json.dumps(list(entries), ensure_ascii=False, indent=2)
