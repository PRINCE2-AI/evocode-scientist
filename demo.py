from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.config import Settings
from app.engine import EvoCodeEngine
from app.storage import ProgramStore


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        settings = Settings(database_path=Path(temp_dir) / "demo.db", generations=2, candidates_per_generation=3)
        engine = EvoCodeEngine(settings=settings, store=ProgramStore(settings.resolved_database_path))
        run = engine.run("bin_packing")
        summary = {
            "problem_id": run.problem_id,
            "metrics": run.metrics,
            "best": run.best_candidate.to_dict() if run.best_candidate else None,
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
