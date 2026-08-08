from __future__ import annotations

from app.schemas import ProblemSpec


POINTS_A = [[0, 0], [1, 0], [1, 1], [0, 1]]
POINTS_B = [[0, 0], [2, 0], [2, 2], [1, 3], [0, 2]]


def _distance(points: list[list[float]], route: list[int]) -> float:
    total = 0.0
    for index, node in enumerate(route):
        nxt = route[(index + 1) % len(route)]
        ax, ay = points[node]
        bx, by = points[nxt]
        total += ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    return total


def tsp_score(output, case: dict) -> float:
    points = case["input"]
    if not isinstance(output, list) or sorted(output) != list(range(len(points))):
        return 0.0
    distance = _distance(points, output)
    reference = case["reference_distance"]
    return max(0.0, min(1.0, reference / max(distance, 1e-9)))


TSP_BASELINE = """
def solve(points):
    if not points:
        return []
    unused = set(range(1, len(points)))
    route = [0]
    while unused:
        current = route[-1]
        cx, cy = points[current]
        nxt = min(unused, key=lambda i: (points[i][0] - cx) ** 2 + (points[i][1] - cy) ** 2)
        route.append(nxt)
        unused.remove(nxt)
    return route
"""


TSP = ProblemSpec(
    id="tsp",
    name="Traveling Salesman Heuristic",
    description="Return a route visiting each point once. Lower tour distance receives higher fitness.",
    function_name="solve",
    tests=(
        {"input": POINTS_A, "expected": None, "reference_distance": 4.0},
        {"input": POINTS_B, "expected": None, "reference_distance": 8.8284},
    ),
    baseline_code=TSP_BASELINE,
    scorer=tsp_score,
)
