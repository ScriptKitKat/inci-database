"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    remote_supabase_url: str | None = None
    remote_supabase_publishable_key: str | None = None
    anthropic_api_key: str | None = None

    judge_model: str = "claude-sonnet-4-6"
    judge_max_tokens: int = 1024
    judge_temperature: float = 0.0
    describe_model: str = "claude-haiku-4-5-20251001"
    describe_max_tokens: int = 300

    # match_ingredient() returns >=0.98 only for canonical/alias exact hits.
    exact_match_confidence: float = 0.98
    # Fuzzy candidates below this are not even offered to the LLM as hypotheses.
    fuzzy_hypothesis_threshold: float = 0.85
    # Minimum LLM confidence per verdict; creation is held to a higher bar.
    match_confirm_threshold: float = 0.85
    new_ingredient_confirm_threshold: float = 0.90
    junk_confidence_threshold: float = 0.90

    product_overlap_threshold: float = 0.90
    trusted_product_domains: str = (
        "incidecoder.com,sephora.com,ulta.com,boots.com,lookfantastic.com,oliveyoung.com"
    )
    # Formula overlap that requires curator review when the product name differs.
    product_formula_similarity_threshold: float = 0.95
    claim_limit: int = 25
    max_attempts: int = 3
    purge_days: int = 30
    # A `triaging` claim older than this is a crashed worker; release it.
    stale_claim_minutes: int = 30
    verification_batch_max_requests: int = 10_000
    verification_batch_max_bytes: int = 20_000_000

    # Fall back to synchronous Messages calls for product verification if
    # web_search inside the Batch API misbehaves.
    sync_product_verification: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
