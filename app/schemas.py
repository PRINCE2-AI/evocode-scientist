from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable


class CandidateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class ProblemSpec:
    id: str
    name: str
    description: str
    function_name: str
    tests: tuple[dict[str, Any], ...]
    baseline_code: str
    scorer: Callable[[Any, dict[str, Any]], float]
    target: str = "maximize"


@dataclass(frozen=True)
class SandboxResult:
    status: CandidateStatus
    outputs: tuple[Any, ...] = ()
    runtime_ms: float = 0.0
    error: str = ""
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class EvaluationResult:
    problem_id: str
    status: CandidateStatus
    score: float
    correctness: float
    quality: float
    runtime_ms: float
    error: str = ""
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class Candidate:
    id: str
    problem_id: str
    code: str
    generation: int
    parent_ids: tuple[str, ...] = ()
    strategy: str = "seed"
    prompt: str = ""
    model: str = "local"
    evaluation: EvaluationResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evaluation"] = self.evaluation.to_dict() if self.evaluation else None
        return data


@dataclass(frozen=True)
class EvolutionRun:
    problem_id: str
    generations: int
    candidates: tuple[Candidate, ...]
    best_candidate: Candidate | None
    metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "generations": self.generations,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "best_candidate": self.best_candidate.to_dict() if self.best_candidate else None,
            "metrics": self.metrics,
        }
