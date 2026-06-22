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
    ncbi_api_key: str | None = None

    data_dir: Path = Field(default=Path("../data/raw"))
    obf_taxonomy_file: str = "ingredients-cosing-obf.txt"
    obf_dump_file: str = "openbeautyfacts-products.jsonl.gz"

    obf_match_threshold: float = 0.92
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def obf_taxonomy_path(self) -> Path:
        return self.data_dir / self.obf_taxonomy_file

    @property
    def obf_dump_path(self) -> Path:
        return self.data_dir / self.obf_dump_file


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
