from __future__ import annotations

from app.schemas import ProblemSpec


def _flatten(bins):
    values = []
    for bin_items in bins:
        values.extend(bin_items)
    return sorted(values)


def bin_packing_score(output, case: dict) -> float:
    items, capacity = case["args"]
    if not isinstance(output, list):
        return 0.0
    if _flatten(output) != sorted(items):
        return 0.0
    for bin_items in output:
        if not isinstance(bin_items, list) or sum(bin_items) > capacity:
            return 0.0
    optimal_bins = case["optimal_bins"]
    used = len(output)
    return max(0.0, min(1.0, optimal_bins / max(used, 1)))


BIN_PACKING_BASELINE = """
def solve(items, capacity):
    bins = []
    for item in items:
        placed = False
        for bin_items in bins:
            if sum(bin_items) + item <= capacity:
                bin_items.append(item)
                placed = True
                break
        if not placed:
            bins.append([item])
    return bins
"""


BIN_PACKING = ProblemSpec(
    id="bin_packing",
    name="Bin Packing Heuristic",
    description="Pack items into bins without exceeding capacity. Fewer bins receive higher fitness.",
    function_name="solve",
    tests=(
        {"args": [[4, 8, 1, 4, 2, 1], 10], "expected": None, "optimal_bins": 2},
        {"args": [[9, 8, 2, 2, 5, 4], 10], "expected": None, "optimal_bins": 3},
    ),
    baseline_code=BIN_PACKING_BASELINE,
    scorer=bin_packing_score,
)
