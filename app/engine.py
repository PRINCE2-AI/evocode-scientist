from __future__ import annotations

from app.code_utils import code_hash
from app.config import Settings, get_settings
from app.evaluator import CandidateEvaluator
from app.evolution import EvolutionStrategy
from app.llm import CodeGenerator
from app.metrics import summarize_candidates
from app.problems import get_problem
from app.sandbox import SandboxExecutor
from app.schemas import Candidate, EvolutionRun
from app.storage import ProgramStore


class EvoCodeEngine:
    def __init__(self, settings: Settings | None = None, store: ProgramStore | None = None) -> None:
        self.settings = settings or get_settings()
        self.sandbox = SandboxExecutor(timeout_seconds=self.settings.sandbox_timeout_seconds)
        self.evaluator = CandidateEvaluator(self.sandbox)
        self.strategy = EvolutionStrategy()
        self.generator = CodeGenerator(self.settings.openai_api_key, self.settings.openai_model)
        self.store = store or ProgramStore(self.settings.resolved_database_path)

    def run(
        self,
        problem_id: str,
        generations: int | None = None,
        candidates_per_generation: int | None = None,
    ) -> EvolutionRun:
        problem = get_problem(problem_id)
        generation_count = generations if generations is not None else self.settings.generations
        per_generation = candidates_per_generation or self.settings.candidates_per_generation

        seed = Candidate(
            id=code_hash(f"{problem.id}:seed:{problem.baseline_code}"),
            problem_id=problem.id,
            code=problem.baseline_code,
            generation=0,
            strategy="baseline_seed",
            model="local",
        )
        evaluated_seed = self._evaluate_and_store(seed)
        population = [evaluated_seed]
        all_candidates = [evaluated_seed]

        for generation in range(1, generation_count + 1):
            elites = self.strategy.select_elites(population, limit=max(1, min(3, len(population))))
            children: list[Candidate] = []
            for elite in elites:
                children.append(self.generator.generate_mutation(problem, elite, generation))
                remaining = max(0, per_generation - len(children))
                if remaining:
                    children.extend(self.strategy.build_local_mutations(elite, generation, count=min(remaining, 2)))
                if len(children) >= per_generation:
                    break
            evaluated_children = [self._evaluate_and_store(child) for child in children[:per_generation]]
            all_candidates.extend(evaluated_children)
            population = self.strategy.select_elites(population + evaluated_children, limit=self.settings.population_size)

        best = self.strategy.select_elites(all_candidates, limit=1)[0] if all_candidates else None
        return EvolutionRun(
            problem_id=problem.id,
            generations=generation_count,
            candidates=tuple(all_candidates),
            best_candidate=best,
            metrics=summarize_candidates(all_candidates),
        )

    def _evaluate_and_store(self, candidate: Candidate) -> Candidate:
        problem = get_problem(candidate.problem_id)
        evaluation = self.evaluator.evaluate(candidate.code, problem)
        evaluated = Candidate(
            id=candidate.id,
            problem_id=candidate.problem_id,
            code=candidate.code,
            generation=candidate.generation,
            parent_ids=candidate.parent_ids,
            strategy=candidate.strategy,
            prompt=candidate.prompt,
            model=candidate.model,
            evaluation=evaluation,
            metadata=candidate.metadata,
        )
        self.store.save_candidate(evaluated)
        return evaluated
