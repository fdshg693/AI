from model_select.dominance import filter_pareto_frontier
from model_select.rank import group_by_bucket


def test_bucket_boundary_exact_minimum():
    items = [{"coding_index": 65}]
    buckets = group_by_bucket(items, lambda m: m["coding_index"], minimum=65, step=3)
    assert list(buckets.keys()) == [(65, 68)]


def test_bucket_boundary_upper_edge_belongs_to_next_bucket():
    items = [{"coding_index": 68}]
    buckets = group_by_bucket(items, lambda m: m["coding_index"], minimum=65, step=3)
    assert list(buckets.keys()) == [(68, 71)]


def test_bucket_below_minimum_excluded():
    items = [{"coding_index": 64.9}]
    buckets = group_by_bucket(items, lambda m: m["coding_index"], minimum=65, step=3)
    assert buckets == {}


def test_bucket_groups_multiple_items_together():
    items = [{"coding_index": 65.5}, {"coding_index": 67.9}, {"coding_index": 68.0}]
    buckets = group_by_bucket(items, lambda m: m["coding_index"], minimum=65, step=3)
    assert len(buckets[(65, 68)]) == 2
    assert len(buckets[(68, 71)]) == 1


def test_pareto_excludes_strictly_dominated_model():
    items = [
        {"name": "cheap-and-good", "price": 1.0, "metric": 80},
        {"name": "expensive-and-worse", "price": 2.0, "metric": 70},
    ]
    result = filter_pareto_frontier(items, lambda m: m["price"], lambda m: m["metric"])
    assert result == [items[0]]


def test_pareto_keeps_non_dominated_tradeoffs():
    items = [
        {"name": "cheaper-but-weaker", "price": 1.0, "metric": 70},
        {"name": "pricier-but-stronger", "price": 2.0, "metric": 80},
    ]
    result = filter_pareto_frontier(items, lambda m: m["price"], lambda m: m["metric"])
    assert result == items


def test_pareto_keeps_both_when_fully_tied():
    items = [
        {"name": "twin-a", "price": 1.0, "metric": 80},
        {"name": "twin-b", "price": 1.0, "metric": 80},
    ]
    result = filter_pareto_frontier(items, lambda m: m["price"], lambda m: m["metric"])
    assert result == items


def test_pareto_excludes_when_dominated_by_strictly_cheaper_equal_metric():
    items = [
        {"name": "cheaper", "price": 1.0, "metric": 80},
        {"name": "same-metric-pricier", "price": 2.0, "metric": 80},
    ]
    result = filter_pareto_frontier(items, lambda m: m["price"], lambda m: m["metric"])
    assert result == [items[0]]
