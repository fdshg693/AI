"""``model-select``のエントリポイント。

fetch -> scope -> rank(coding_index) -> dominance(入力軸) / dominance(出力軸) -> render -> ファイル書き出し
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from model_select.dominance import filter_pareto_frontier
from model_select.fetch import fetch_models
from model_select.pricing import per_million_tokens, worst_case_price_per_token
from model_select.rank import group_by_bucket
from model_select.render import render_report
from model_select.scope import filter_in_scope

CODING_INDEX_MINIMUM = 65
CODING_INDEX_STEP = 3

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "output" / "report.html"


def _coding_index(model: dict) -> float:
    return model["benchmarks"]["artificial_analysis"]["coding_index"]


def _build_axis_view(
    buckets: dict[tuple[float, float], list[dict]], price_field: str
) -> dict[tuple[float, float], list[dict]]:
    """1軸（``"prompt"``または``"completion"``）分の、bucket→Pareto frontier行リストを組み立てる。"""

    def price_of(model: dict) -> float:
        return per_million_tokens(worst_case_price_per_token(model, price_field))

    view: dict[tuple[float, float], list[dict]] = {}
    for bounds, models in buckets.items():
        frontier = filter_pareto_frontier(models, price_of, _coding_index)
        rows = [
            {
                "id": model["id"],
                "name": model.get("name", model["id"]),
                "coding_index": _coding_index(model),
                "price_per_million": price_of(model),
            }
            for model in frontier
        ]
        rows.sort(key=lambda row: row["price_per_million"])
        view[bounds] = rows
    return view


def main() -> None:
    models = filter_in_scope(fetch_models())
    buckets = group_by_bucket(models, _coding_index, CODING_INDEX_MINIMUM, CODING_INDEX_STEP)

    sections = [
        ("入力重視（prompt価格が安い順）", len(models), _build_axis_view(buckets, "prompt")),
        (
            "出力重視（completion価格が安い順）",
            len(models),
            _build_axis_view(buckets, "completion"),
        ),
    ]
    html_report = render_report(datetime.now(timezone.utc), sections)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html_report, encoding="utf-8")
    print(str(OUTPUT_PATH))


if __name__ == "__main__":
    main()
