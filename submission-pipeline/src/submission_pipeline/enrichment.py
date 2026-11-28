from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

ShortText = Annotated[str, Field(min_length=1, max_length=500)]


class IngredientEnrichment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    rating: Literal["ew_ew", "okie", "yippe", "wowza"] | None
    functions: list[ShortText] | None = Field(max_length=100)
    quick_facts: list[ShortText] | None = Field(max_length=10)
    summary: str | None = Field(min_length=1, max_length=2000)
    details: str | None = Field(min_length=1, max_length=10000)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=500)

    @field_validator("summary", "details", "rationale")
    @classmethod
    def nonblank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("blank text")
        return value

    @field_validator("functions", "quick_facts")
    @classmethod
    def unique_nonblank(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and (
            len(value) != len(set(value)) or any(not v.strip() for v in value)
        ):
            raise ValueError("blank or duplicate values")
        return value


def parse_enrichment(text: str, allowed_functions: list[str]) -> IngredientEnrichment | None:
    try:
        result = IngredientEnrichment.model_validate_json(text)
    except ValidationError:
        return None
    if not set(result.functions or []).issubset(allowed_functions):
        return None
    return result


def review_reason(result: IngredientEnrichment | None, threshold: float) -> str | None:
    if result is None:
        return "invalid_enrichment_result"
    if result.confidence < threshold:
        return "enrichment_confidence_below_threshold"
    return None
