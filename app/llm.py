from __future__ import annotations

from app.code_utils import code_hash, extract_code
from app.prompts import mutation_prompt
from app.schemas import Candidate, ProblemSpec


class CodeGenerator:
    def __init__(self, api_key: str = "", model: str = "gpt-4.1-mini") -> None:
        self.api_key = api_key
        self.model = model

    def generate_mutation(self, problem: ProblemSpec, parent: Candidate, generation: int) -> Candidate:
        prompt = mutation_prompt(problem, parent)
        if not self.api_key:
            code = self._fallback(problem, parent)
            model = "local"
        else:
            code = self._openai(prompt, parent.code)
            model = self.model
        return Candidate(
            id=code_hash(f"{parent.id}:{generation}:{model}:{code}"),
            problem_id=problem.id,
            code=code,
            generation=generation,
            parent_ids=(parent.id,),
            strategy="llm_mutation" if self.api_key else "local_fallback",
            prompt=prompt,
            model=model,
        )

    @staticmethod
    def _fallback(problem: ProblemSpec, parent: Candidate) -> str:
        if problem.id == "bin_packing":
            return """def solve(items, capacity):
    bins = []
    for item in sorted(items, reverse=True):
        placed = False
        for bucket in bins:
            if sum(bucket) + item <= capacity:
                bucket.append(item)
                placed = True
                break
        if not placed:
            bins.append([item])
    return bins
"""
        if problem.id == "tsp":
            return parent.code
        if problem.id == "string_compression":
            return parent.code
        return parent.code

    def _openai(self, prompt: str, fallback_code: str) -> str:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=900,
            )
            content = response.choices[0].message.content or fallback_code
            return extract_code(content)
        except Exception:
            return fallback_code
