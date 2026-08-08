from __future__ import annotations

import streamlit as st

from app.engine import EvoCodeEngine
from app.problems import PROBLEM_REGISTRY


st.set_page_config(page_title="EvoCode Scientist", page_icon="EC", layout="wide")
st.title("EvoCode Scientist")
st.caption("AlphaEvolve-inspired coding agent with sandboxed execution and automated scoring.")

problem_id = st.sidebar.selectbox("Problem", sorted(PROBLEM_REGISTRY.keys()))
generations = st.sidebar.slider("Generations", 0, 10, 2)
candidates_per_generation = st.sidebar.slider("Candidates per generation", 1, 10, 3)

if st.sidebar.button("Run evolution", type="primary"):
    engine = EvoCodeEngine()
    run = engine.run(problem_id, generations=generations, candidates_per_generation=candidates_per_generation)
    st.subheader("Metrics")
    st.json(run.metrics)

    rows = []
    for candidate in run.candidates:
        evaluation = candidate.evaluation
        rows.append(
            {
                "id": candidate.id,
                "generation": candidate.generation,
                "strategy": candidate.strategy,
                "model": candidate.model,
                "score": evaluation.score if evaluation else 0.0,
                "correctness": evaluation.correctness if evaluation else 0.0,
                "quality": evaluation.quality if evaluation else 0.0,
                "status": evaluation.status.value if evaluation else "pending",
            }
        )
    st.subheader("Leaderboard")
    st.dataframe(sorted(rows, key=lambda item: item["score"], reverse=True), use_container_width=True)

    if run.best_candidate:
        st.subheader("Best Candidate")
        st.code(run.best_candidate.code, language="python")
        st.json(run.best_candidate.evaluation.to_dict() if run.best_candidate.evaluation else {})
else:
    st.info("Select a benchmark and run the evolutionary loop.")
