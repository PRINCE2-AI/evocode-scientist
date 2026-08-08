from __future__ import annotations

from app.schemas import Candidate, ProblemSpec


def mutation_prompt(problem: ProblemSpec, parent: Candidate) -> str:
    score = parent.evaluation.score if parent.evaluation else 0.0
    return f"""You are improving a Python function for an evolutionary coding benchmark.

Problem:
{problem.description}

Function required:
def {problem.function_name}(...):

Current candidate score: {score}

Current code:
```python
{parent.code}
```

Return only Python code. Keep it deterministic. Do not import unsafe modules. Define `{problem.function_name}`.
"""
