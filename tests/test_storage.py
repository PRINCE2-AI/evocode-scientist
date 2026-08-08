from app.code_utils import code_hash
from app.evaluator import CandidateEvaluator
from app.sandbox import SandboxExecutor
from app.schemas import Candidate
from app.storage import ProgramStore
from problems.string_compression import STRING_COMPRESSION


def test_store_saves_and_loads_leaderboard(tmp_path) -> None:
    store = ProgramStore(tmp_path / "programs.db")
    evaluation = CandidateEvaluator(SandboxExecutor()).evaluate(
        STRING_COMPRESSION.baseline_code,
        STRING_COMPRESSION,
    )
    candidate = Candidate(
        id=code_hash("candidate"),
        problem_id=STRING_COMPRESSION.id,
        code=STRING_COMPRESSION.baseline_code,
        generation=0,
        evaluation=evaluation,
    )
    store.save_candidate(candidate)
    loaded = store.leaderboard(STRING_COMPRESSION.id)
    assert loaded
    assert loaded[0].id == candidate.id
    assert loaded[0].evaluation.score == evaluation.score
