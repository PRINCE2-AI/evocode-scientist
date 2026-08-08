from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Install API dependencies with `pip install -r requirements.txt`.") from exc

from app.config import get_settings
from app.engine import EvoCodeEngine
from app.problems import get_problem, list_problems


class RunRequest(BaseModel):
    problem_id: str = Field(default="bin_packing")
    generations: int = Field(default=2, ge=0, le=20)
    candidates_per_generation: int = Field(default=3, ge=1, le=20)


api = FastAPI(
    title="EvoCode Scientist",
    description="AlphaEvolve-inspired evolutionary coding agent with sandboxed execution and automated scoring.",
    version="0.1.0",
)


@api.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "openai_enabled": settings.openai_enabled,
        "model": settings.openai_model,
        "database_path": str(settings.resolved_database_path),
    }


@api.get("/problems")
def problems() -> list[dict[str, str]]:
    return list_problems()


@api.get("/problems/{problem_id}")
def problem(problem_id: str) -> dict[str, Any]:
    spec = get_problem(problem_id)
    return {
        "id": spec.id,
        "name": spec.name,
        "description": spec.description,
        "function_name": spec.function_name,
        "test_count": len(spec.tests),
    }


@api.post("/run")
def run(request: RunRequest) -> dict[str, Any]:
    engine = EvoCodeEngine()
    return engine.run(
        request.problem_id,
        generations=request.generations,
        candidates_per_generation=request.candidates_per_generation,
    ).to_dict()


@api.get("/leaderboard/{problem_id}")
def leaderboard(problem_id: str, limit: int = 10) -> list[dict[str, Any]]:
    engine = EvoCodeEngine()
    return [candidate.to_dict() for candidate in engine.store.leaderboard(problem_id, limit=limit)]
