from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.schemas import Candidate, EvaluationResult


class ProgramStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    problem_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    parent_ids TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    model TEXT NOT NULL,
                    evaluation TEXT,
                    metadata TEXT NOT NULL
                )
                """
            )

    def save_candidate(self, candidate: Candidate) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO candidates
                (id, problem_id, code, generation, parent_ids, strategy, prompt, model, evaluation, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.id,
                    candidate.problem_id,
                    candidate.code,
                    candidate.generation,
                    json.dumps(candidate.parent_ids),
                    candidate.strategy,
                    candidate.prompt,
                    candidate.model,
                    json.dumps(candidate.evaluation.to_dict()) if candidate.evaluation else None,
                    json.dumps(candidate.metadata),
                ),
            )

    def leaderboard(self, problem_id: str, limit: int = 10) -> list[Candidate]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM candidates WHERE problem_id = ? ORDER BY json_extract(evaluation, '$.score') DESC LIMIT ?",
                (problem_id, limit),
            ).fetchall()
        return [self._candidate_from_row(row) for row in rows]

    def list_candidates(self, problem_id: str | None = None) -> list[Candidate]:
        query = "SELECT * FROM candidates"
        args: tuple[object, ...] = ()
        if problem_id:
            query += " WHERE problem_id = ?"
            args = (problem_id,)
        query += " ORDER BY generation ASC"
        with self._connect() as conn:
            rows = conn.execute(query, args).fetchall()
        return [self._candidate_from_row(row) for row in rows]

    @staticmethod
    def _candidate_from_row(row: sqlite3.Row) -> Candidate:
        evaluation_data = json.loads(row["evaluation"]) if row["evaluation"] else None
        evaluation = None
        if evaluation_data:
            from app.schemas import CandidateStatus

            evaluation_data["status"] = CandidateStatus(evaluation_data["status"])
            evaluation_data["details"] = tuple(evaluation_data.get("details", ()))
            evaluation = EvaluationResult(**evaluation_data)
        return Candidate(
            id=row["id"],
            problem_id=row["problem_id"],
            code=row["code"],
            generation=row["generation"],
            parent_ids=tuple(json.loads(row["parent_ids"])),
            strategy=row["strategy"],
            prompt=row["prompt"],
            model=row["model"],
            evaluation=evaluation,
            metadata=json.loads(row["metadata"]),
        )
