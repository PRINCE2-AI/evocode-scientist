from pathlib import Path

from app.config import Settings
from app.engine import EvoCodeEngine
from app.storage import ProgramStore


def test_engine_runs_evolution_loop(tmp_path) -> None:
    settings = Settings(database_path=Path(tmp_path) / "run.db", generations=1, candidates_per_generation=2)
    engine = EvoCodeEngine(settings=settings, store=ProgramStore(settings.resolved_database_path))
    run = engine.run("string_compression", generations=1, candidates_per_generation=2)
    assert run.best_candidate is not None
    assert run.metrics["candidate_count"] >= 2
    assert run.best_candidate.evaluation.score > 0.5
