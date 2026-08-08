from __future__ import annotations

from app.schemas import ProblemSpec


def knapsack_score(output, case: dict) -> float:
    expected = case["expected"]
    if output != expected:
        return 0.0
    return 1.0


KNAPSACK_BASELINE = """
def solve(items, capacity):
    n = len(items)
    dp = [0] * (capacity + 1)
    for weight, value in items:
        for cap in range(capacity, weight - 1, -1):
            candidate = dp[cap - weight] + value
            if candidate > dp[cap]:
                dp[cap] = candidate
    return max(dp)
"""


KNAPSACK = ProblemSpec(
    id="knapsack",
    name="0/1 Knapsack",
    description="Return the maximum value achievable under the capacity limit.",
    function_name="solve",
    tests=(
        {"args": [[[2, 3], [3, 4], [4, 5], [5, 8]], 5], "expected": 8},
        {"args": [[[1, 1], [2, 6], [5, 18], [6, 22]], 7], "expected": 24},
    ),
    baseline_code=KNAPSACK_BASELINE,
    scorer=knapsack_score,
)
