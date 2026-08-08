from app.evaluator import CandidateEvaluator
from app.sandbox import SandboxExecutor
from app.schemas import CandidateStatus
from problems.knapsack import KNAPSACK


def test_evaluator_scores_correct_candidate() -> None:
    evaluator = CandidateEvaluator(SandboxExecutor(timeout_seconds=2))
    result = evaluator.evaluate(KNAPSACK.baseline_code, KNAPSACK)
    assert result.status == CandidateStatus.PASSED
    assert result.correctness == 1.0
    assert result.score > 0.7
