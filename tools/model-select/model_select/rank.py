"""指標値に基づくbucket（半開区間）分類。指標名を特定のものにベタ書きしない汎用関数。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def bucket_bounds(value: float, minimum: float, step: float) -> tuple[float, float]:
    """``value``が属する半開区間``[low, low+step)``の境界を返す。

    ``value``は``minimum``以上であることを前提とする（呼び出し側で足切り済みのこと）。
    """
    steps_above_minimum = int((value - minimum) // step)
    low = minimum + steps_above_minimum * step
    return low, low + step


def group_by_bucket(
    items: list[T],
    metric_of: Callable[[T], float],
    minimum: float,
    step: float,
) -> dict[tuple[float, float], list[T]]:
    """``metric_of(item)``が``minimum``未満の要素を除外し、残りを``step``刻みのbucketにグルーピングする。

    戻り値は``(low, high)``の境界タプルをキーとする辞書（bucket境界の昇順ではなく、出現順）。
    """
    buckets: dict[tuple[float, float], list[T]] = {}
    for item in items:
        metric = metric_of(item)
        if metric < minimum:
            continue
        bounds = bucket_bounds(metric, minimum, step)
        buckets.setdefault(bounds, []).append(item)
    return buckets
