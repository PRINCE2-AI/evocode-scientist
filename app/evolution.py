from __future__ import annotations

from app.code_utils import code_hash
from app.schemas import Candidate


class EvolutionStrategy:
    def select_elites(self, candidates: list[Candidate], limit: int = 3) -> list[Candidate]:
        return sorted(
            candidates,
            key=lambda candidate: candidate.evaluation.score if candidate.evaluation else 0.0,
            reverse=True,
        )[:limit]

    def build_local_mutations(self, parent: Candidate, generation: int, count: int = 3) -> list[Candidate]:
        variants = [
            self._inject_comment(parent.code, "prefer simple deterministic logic"),
            self._tighten_loops(parent.code),
            self._rename_locals(parent.code),
        ][:count]
        children: list[Candidate] = []
        for index, code in enumerate(variants):
            children.append(
                Candidate(
                    id=code_hash(f"{parent.id}:{generation}:{index}:{code}"),
                    problem_id=parent.problem_id,
                    code=code,
                    generation=generation,
                    parent_ids=(parent.id,),
                    strategy=f"local_mutation_{index}",
                    model="local",
                )
            )
        return children

    @staticmethod
    def _inject_comment(code: str, comment: str) -> str:
        lines = code.strip().splitlines()
        if not lines:
            return code
        return "\n".join([f"# mutation: {comment}", *lines]) + "\n"

    @staticmethod
    def _tighten_loops(code: str) -> str:
        return code.replace("for i in range(len(", "for i in range(len(")

    @staticmethod
    def _rename_locals(code: str) -> str:
        return code.replace("best", "best_value").replace("result", "answer")
