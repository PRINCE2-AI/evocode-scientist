from __future__ import annotations

from app.schemas import Candidate


def summarize_candidates(candidates: list[Candidate]) -> dict[str, float]:
    if not candidates:
        return {"candidate_count": 0.0, "best_score": 0.0, "avg_score": 0.0}
    scores = [candidate.evaluation.score for candidate in candidates if candidate.evaluation]
    return {
        "candidate_count": float(len(candidates)),
        "best_score": round(max(scores) if scores else 0.0, 4),
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "passed_count": float(sum(1 for candidate in candidates if candidate.evaluation and candidate.evaluation.correctness == 1.0)),
    }
