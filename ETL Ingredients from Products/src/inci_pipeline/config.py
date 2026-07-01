"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str

    anthropic_api_key: str | None = None
    ingredient_judge_model: str = "claude-sonnet-4-6"
    ingredient_judge_temperature: float = 0.0
    ingredient_judge_max_tokens: int = 800
    ingredient_judge_poll_interval_seconds: int = 30
    ingredient_judge_poll_timeout_seconds: int = 3600

    ingredient_lookup_enable_pubchem: bool = True
    ingredient_lookup_enable_wikidata: bool = False
    ingredient_lookup_enable_specialchem: bool = True
    ingredient_lookup_enable_incidecoder: bool = True
    ingredient_lookup_max_retry_after_seconds: float = 10.0

    data_dir: Path = Field(default=Path("../data/raw"))
    obf_taxonomy_file: str = "ingredients-cosing-obf.txt"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def obf_taxonomy_path(self) -> Path:
        return self.data_dir / self.obf_taxonomy_file

@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
