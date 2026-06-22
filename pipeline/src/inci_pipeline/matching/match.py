"""Token -> ingredient resolver.

Delegates to the `match_ingredient` Postgres function so the Python
pipeline and any future API layer use the same definition. Tested
indirectly via stage integration tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ..db import client


@dataclass(frozen=True)
class MatchResult:
    ingredient_id: UUID
    match_type: str
    confidence: float


def match_token(token: str) -> MatchResult | None:
    if not token or not token.strip():
        return None
    res = client().rpc("match_ingredient", {"input": token}).execute()
    rows = res.data or []
    if not rows:
        return None
    row = rows[0]
    return MatchResult(
        ingredient_id=UUID(row["ingredient_id"]),
        match_type=row["match_type"],
        confidence=float(row["confidence"]),
    )
