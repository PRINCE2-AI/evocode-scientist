# Paper Notes

Paper: AlphaEvolve: A coding agent for scientific and algorithmic discovery

Link: https://arxiv.org/abs/2506.13131

## Concepts Used

- Program generation by an LLM.
- Automated execution-based evaluation.
- Population of candidate programs.
- Iterative improvement using feedback from scores.
- Program database and candidate lineage.

## What This Project Implements

- A practical Python implementation of the loop.
- Deterministic benchmark tasks.
- Subprocess sandbox execution.
- SQLite storage for candidate history.
- Optional OpenAI API code mutation.

## What It Does Not Claim

- It does not reproduce DeepMind's full AlphaEvolve system.
- It does not claim scientific discovery results.
- It does not execute untrusted code with production-grade isolation.
