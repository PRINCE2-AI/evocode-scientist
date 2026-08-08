from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parents[1]
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    database_path: Path = Path(os.getenv("EVOCODE_DB_PATH", "data/evocode.db"))
    sandbox_timeout_seconds: float = float(os.getenv("EVOCODE_SANDBOX_TIMEOUT", "2.0"))
    population_size: int = int(os.getenv("EVOCODE_POPULATION_SIZE", "6"))
    generations: int = int(os.getenv("EVOCODE_GENERATIONS", "3"))
    candidates_per_generation: int = int(os.getenv("EVOCODE_CANDIDATES_PER_GENERATION", "4"))

    @property
    def resolved_database_path(self) -> Path:
        if self.database_path.is_absolute():
            return self.database_path
        return self.project_root / self.database_path

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    return Settings()
