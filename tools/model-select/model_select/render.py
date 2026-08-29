"""自己完結HTML生成（サーバー・JS不要、Python側でテーブルHTMLを直接組み立てる）。"""

from __future__ import annotations

import html
from datetime import datetime


def render_report(
    generated_at: datetime,
    sections: list[tuple[str, int, dict[tuple[float, float], list[dict]]]],
) -> str:
    """自己完結HTMLレポートを組み立てる。

    ``sections``は``(セクションタイトル, スコープ内対象モデル総数, bucket→行リストの辞書)``のリスト。
    bucketは``(low, high)``タプルをキーとし、値の行リストは価格の安い順・Pareto frontier上の
    モデルのみである前提（``dominance.filter_pareto_frontier``適用済み）。モデルが0件のbucketは
    見出しごと省略する。
    """
    body_parts = [_render_section(title, total, buckets) for title, total, buckets in sections]
    return _PAGE_TEMPLATE.format(
        generated_at=generated_at.isoformat(timespec="seconds"),
        sections="\n".join(body_parts),
    )


def _render_section(
    title: str, total_in_scope: int, buckets: dict[tuple[float, float], list[dict]]
) -> str:
    bucket_html = "\n".join(
        _render_bucket(low, high, rows) for (low, high), rows in sorted(buckets.items()) if rows
    )
    return f"""
<section>
  <h2>{html.escape(title)}</h2>
  <p class="summary">スコープ内対象モデル総数（ランク分け前）: {total_in_scope}件</p>
  {bucket_html}
</section>
"""


def _render_bucket(low: float, high: float, rows: list[dict]) -> str:
    row_html = "\n".join(_render_row(row) for row in rows)
    return f"""
<h3>coding_index [{low:g}, {high:g})</h3>
<table>
  <thead><tr><th>モデル</th><th>ID</th><th>coding_index</th><th>価格（$/M tokens）</th></tr></thead>
  <tbody>
  {row_html}
  </tbody>
</table>
"""


def _render_row(row: dict) -> str:
    return (
        "<tr>"
        f"<td>{html.escape(row['name'])}</td>"
        f"<td>{html.escape(row['id'])}</td>"
        f"<td>{row['coding_index']:g}</td>"
        f"<td>{row['price_per_million']:.2f}</td>"
        "</tr>"
    )


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>model-select report</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; margin-bottom: 1.5rem; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; }}
h3 {{ margin-top: 1.5rem; }}
.summary {{ color: #555; }}
footer {{ margin-top: 2rem; color: #888; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>model-select report</h1>
{sections}
<footer>生成日時: {generated_at}</footer>
</body>
</html>
"""
