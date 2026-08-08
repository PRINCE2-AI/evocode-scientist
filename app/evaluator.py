from __future__ import annotations

from app.sandbox import SandboxExecutor
from app.schemas import CandidateStatus, EvaluationResult, ProblemSpec


class CandidateEvaluator:
    def __init__(self, sandbox: SandboxExecutor) -> None:
        self.sandbox = sandbox

    def evaluate(self, code: str, problem: ProblemSpec) -> EvaluationResult:
        sandbox_result = self.sandbox.run(code, problem)
        if sandbox_result.status != CandidateStatus.PASSED:
            return EvaluationResult(
                problem_id=problem.id,
                status=sandbox_result.status,
                score=0.0,
                correctness=0.0,
                quality=0.0,
                runtime_ms=sandbox_result.runtime_ms,
                error=sandbox_result.error,
            )

        details: list[dict[str, object]] = []
        quality_total = 0.0
        correct_total = 0.0
        for case, output in zip(problem.tests, sandbox_result.outputs):
            expected = case.get("expected")
            if expected is None:
                quality = problem.scorer(output, case)
                is_correct = quality > 0.0
            else:
                is_correct = output == expected
                quality = problem.scorer(output, case) if is_correct else 0.0
            correctness = 1.0 if is_correct else 0.0
            correct_total += correctness
            quality_total += quality
            details.append(
                {
                    "input": case.get("input", case.get("args", case.get("kwargs"))),
                    "expected": expected,
                    "output": output,
                    "correct": is_correct,
                    "quality": round(quality, 4),
                }
            )

        total = max(len(problem.tests), 1)
        correctness_score = correct_total / total
        quality_score = quality_total / total
        runtime_penalty = min(sandbox_result.runtime_ms / 5000.0, 0.2)
        score = max(0.0, (0.75 * correctness_score) + (0.25 * quality_score) - runtime_penalty)
        status = CandidateStatus.PASSED if correctness_score == 1.0 else CandidateStatus.FAILED
        return EvaluationResult(
            problem_id=problem.id,
            status=status,
            score=round(score, 4),
            correctness=round(correctness_score, 4),
            quality=round(quality_score, 4),
            runtime_ms=sandbox_result.runtime_ms,
            details=tuple(details),
        )
