"""markdown / json 整形。"""

from __future__ import annotations

import json
from typing import TypedDict


class ResultEntry(TypedDict):
    path: str
    resolved_path: str
    success: bool
    response: str | None
    error: str | None


def format_markdown(entries: list[ResultEntry]) -> str:
    blocks = []
    for entry in entries:
        if entry["success"]:
            body = entry["response"]
        else:
            body = f"⚠ エラー: {entry['error']}"
        blocks.append(f"## {entry['path']}\n\n{body}\n")
    return "\n".join(blocks)


def format_json(entries: list[ResultEntry]) -> str:
    return json.dumps(list(entries), ensure_ascii=False, indent=2)
