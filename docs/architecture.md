# Architecture

EvoCode Scientist is organized around an execution-first agent loop.

```text
ProblemSpec
  -> CodeGenerator
  -> AST validation
  -> SandboxExecutor
  -> CandidateEvaluator
  -> ProgramStore
  -> EvolutionStrategy
  -> next generation
```

The important boundary is between generation and evaluation. The generator may be an LLM or the local deterministic fallback. The evaluator is deterministic and decides whether a candidate survives.

## Core Components

| Component | Responsibility |
| --- | --- |
| `app/engine.py` | Coordinates generation, evaluation, storage, and selection |
| `app/sandbox.py` | Runs candidate code in a temporary subprocess with timeout |
| `app/evaluator.py` | Converts test outputs into correctness, quality, and score |
| `app/evolution.py` | Selects elites and builds local mutations |
| `app/storage.py` | Stores candidate lineage and evaluation results |
| `problems/` | Defines benchmark inputs, baseline code, and scoring |

## Production Gaps

The v1 sandbox is appropriate for local portfolio demos. A production version should add container isolation, memory limits, filesystem/network denial, and stronger syscall controls.
