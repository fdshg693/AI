"""スコープ絞り込み: variant除外 + coding_index必須のフィルタ。"""

from __future__ import annotations


def is_variant(model: dict) -> bool:
    """``:free``/`:batch`/`:thinking`等のvariant idかどうか。"""
    return ":" in model["id"]


def has_coding_index(model: dict) -> bool:
    benchmarks = model.get("benchmarks")
    if not benchmarks:
        return False
    artificial_analysis = benchmarks.get("artificial_analysis")
    if not artificial_analysis:
        return False
    return artificial_analysis.get("coding_index") is not None


def filter_in_scope(models: list[dict]) -> list[dict]:
    """variantでなく、かつ``benchmarks.artificial_analysis.coding_index``を持つモデルのみ残す。"""
    return [m for m in models if not is_variant(m) and has_coding_index(m)]
