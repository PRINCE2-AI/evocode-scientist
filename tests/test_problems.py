from app.problems import get_problem, list_problems
from problems.bin_packing import BIN_PACKING, BIN_PACKING_BASELINE, bin_packing_score


def _minimum_bins(items: list[int], capacity: int) -> int:
    best = [len(items)]

    def place(index: int, loads: list[int]) -> None:
        if len(loads) >= best[0]:
            return
        if index == len(items):
            best[0] = len(loads)
            return
        item = items[index]
        seen: set[int] = set()
        for position, load in enumerate(loads):
            if load in seen or load + item > capacity:
                continue
            seen.add(load)
            loads[position] += item
            place(index + 1, loads)
            loads[position] -= item
        loads.append(item)
        place(index + 1, loads)
        loads.pop()

    place(0, [])
    return best[0]


def test_problem_registry_lists_core_benchmarks() -> None:
    ids = {problem["id"] for problem in list_problems()}
    assert {"tsp", "bin_packing", "string_compression", "knapsack"} <= ids


def test_get_problem_returns_spec() -> None:
    problem = get_problem("bin_packing")
    assert problem.function_name == "solve"
    assert problem.tests


def test_bin_packing_targets_match_brute_force_optimum() -> None:
    for case in BIN_PACKING.tests:
        items, capacity = case["args"]
        assert case["optimal_bins"] == _minimum_bins(items, capacity)


def test_bin_packing_baseline_scores_perfectly() -> None:
    namespace: dict[str, object] = {}
    exec(BIN_PACKING_BASELINE, namespace)
    solve = namespace["solve"]
    for case in BIN_PACKING.tests:
        output = solve(*case["args"])
        assert bin_packing_score(output, case) == 1.0
