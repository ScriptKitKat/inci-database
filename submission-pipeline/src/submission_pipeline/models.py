"""Frozen value objects shared across stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Verdict = Literal["matched", "new_ingredient", "junk", "unknown"]
HypothesisKind = Literal["existing", "authoritative"]


@dataclass(frozen=True)
class Evidence:
    """Compact per-source lookup result stored on submission_tokens.evidence."""

    source: str
    found: bool
    canonical: str | None = None
    url: str | None = None
    confidence: float = 0.0
    enrichment: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "found": self.found,
            "canonical": self.canonical,
            "url": self.url,
            "confidence": self.confidence,
            "enrichment": self.enrichment,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Evidence:
        return cls(
            source=data.get("source", ""),
            found=bool(data.get("found")),
            canonical=data.get("canonical"),
            url=data.get("url"),
            confidence=float(data.get("confidence") or 0.0),
            enrichment=dict(data.get("enrichment") or {}),
        )


@dataclass(frozen=True)
class Hypothesis:
    """A spelling anchored to the catalog or an authoritative source.

    The LLM can only pick a hypothesis by id; it can never supply its own
    canonical string.
    """

    id: str
    kind: HypothesisKind
    canonical: str
    source: str
    confidence: float
    ingredient_id: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "canonical": self.canonical,
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class TokenJudgment:
    verdict: Verdict
    choice_id: str | None
    confidence: float
    reason: str


@dataclass(frozen=True)
class ProductFinding:
    """Parsed result of the product web-search verification request."""

    found: bool
    source_name: str | None = None
    source_url: str | None = None
    online_ingredients: list[str] = field(default_factory=list)
