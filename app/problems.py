from __future__ import annotations

from app.schemas import ProblemSpec
from problems.bin_packing import BIN_PACKING
from problems.knapsack import KNAPSACK
from problems.string_compression import STRING_COMPRESSION
from problems.tsp import TSP


PROBLEM_REGISTRY: dict[str, ProblemSpec] = {
    problem.id: problem
    for problem in (
        TSP,
        BIN_PACKING,
        STRING_COMPRESSION,
        KNAPSACK,
    )
}


def list_problems() -> list[dict[str, str]]:
    return [
        {"id": problem.id, "name": problem.name, "description": problem.description}
        for problem in PROBLEM_REGISTRY.values()
    ]


def get_problem(problem_id: str) -> ProblemSpec:
    try:
        return PROBLEM_REGISTRY[problem_id]
    except KeyError as exc:
        available = ", ".join(sorted(PROBLEM_REGISTRY))
        raise ValueError(f"unknown problem_id={problem_id}; available: {available}") from exc
