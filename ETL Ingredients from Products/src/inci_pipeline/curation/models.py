from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


Decision = Literal[
    "keep",
    "merge_into_existing",
    "alias_to_existing",
    "reject_or_quarantine",
    "needs_human",
]


class IngredientEvidence(BaseModel):
    source: str
    lookup_type: str
    found: bool = False
    canonical_name: str | None = None
    normalized_canonical: str | None = None
    url: str | None = None
    confidence: float = 0
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class IngredientCandidate(BaseModel):
    candidate_id: UUID | None = None
    queue_id: UUID | None = None
    source_ingredient_id: UUID
    inci_name: str
    normalized_name: str
    ingredient_created_at: str | None = None


class IngredientEdge(BaseModel):
    source_ingredient_id: UUID
    target_ingredient_id: UUID
    source_normalized_name: str
    target_normalized_name: str
    relationship_type: str
    pg_trgm_similarity: float | None = None
    edit_distance: int | None = None
    token_overlap: float | None = None
    score_margin: float | None = None


class CurationDecision(BaseModel):
    decision: Decision
    target_ingredient_id: UUID | None = None
    canonical_inci_name: str | None = None
    aliases_to_add: list[str] = Field(default_factory=list)
    confidence: float
    reason: str


class ReviewSink:
    def send(self, decision_ids: list[UUID]) -> None:
        raise NotImplementedError


class NoopReviewSink(ReviewSink):
    def send(self, decision_ids: list[UUID]) -> None:
        return None

