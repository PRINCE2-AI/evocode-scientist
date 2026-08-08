from app.problems import get_problem, list_problems


def test_problem_registry_lists_core_benchmarks() -> None:
    ids = {problem["id"] for problem in list_problems()}
    assert {"tsp", "bin_packing", "string_compression", "knapsack"} <= ids


def test_get_problem_returns_spec() -> None:
    problem = get_problem("bin_packing")
    assert problem.function_name == "solve"
    assert problem.tests
