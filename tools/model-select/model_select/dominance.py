"""同一bucket内のPareto最適フィルタ（価格最小化・指標最大化）。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def filter_pareto_frontier(
    items: list[T],
    price_of: Callable[[T], float],
    metric_of: Callable[[T], float],
) -> list[T]:
    """「価格が同じ以下 かつ 指標が同じ以上」で、少なくとも一方が厳密に優れる他要素が存在する
    要素を除外し、Pareto frontier上の要素だけを残す。

    価格・指標が完全に同値の要素同士は互いを支配しない（両方消えることはない）。
    """
    result: list[T] = []
    for candidate in items:
        candidate_price = price_of(candidate)
        candidate_metric = metric_of(candidate)
        dominated = False
        for other in items:
            if other is candidate:
                continue
            other_price = price_of(other)
            other_metric = metric_of(other)
            not_worse = other_price <= candidate_price and other_metric >= candidate_metric
            strictly_better = other_price < candidate_price or other_metric > candidate_metric
            if not_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            result.append(candidate)
    return result
