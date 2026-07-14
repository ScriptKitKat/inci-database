"""Token -> ingredient resolver.

Checks the review database first, then the remote canonical catalog. Remote
matches are accepted automatically only when the catalog reports an exact
canonical or alias match.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re
from uuid import UUID

from supabase import Client, create_client

from . import db
from .config import settings

_PARENTHETICAL_COMMON_NAME = re.compile(r"\s*\([A-Za-z][A-Za-z -]*\)")


@dataclass(frozen=True)
class MatchResult:
    ingredient_id: UUID
    match_type: str
    confidence: float


def match_token(token: str) -> MatchResult | None:
    if not token or not token.strip():
        return None
    local_match = _match(db.client(), token)
    if local_match and local_match.match_type.endswith("_exact"):
        return local_match

    canonical_variant = _PARENTHETICAL_COMMON_NAME.sub("", token).strip()
    if canonical_variant != token.strip():
        variant_match = _match(db.client(), canonical_variant)
        if variant_match and variant_match.match_type.endswith("_exact"):
            return variant_match

    remote = remote_client()
    if remote:
        remote_matches = [_match(remote, token)]
        if canonical_variant != token.strip():
            remote_matches.append(_match(remote, canonical_variant))
        for remote_match in remote_matches:
            if not remote_match or not remote_match.match_type.endswith("_exact"):
                continue
            ingredient = (
                remote.table("ingredients")
                .select("id, inci_name, slug")
                .eq("id", str(remote_match.ingredient_id))
                .single()
                .execute()
                .data
            )
            local_id = db.sync_remote_catalog_ingredient(ingredient)
            return MatchResult(
                ingredient_id=UUID(local_id),
                match_type=remote_match.match_type,
                confidence=remote_match.confidence,
            )
    return local_match


def _match(catalog: Client, token: str) -> MatchResult | None:
    res = catalog.rpc("match_ingredient", {"input": token}).execute()
    rows = res.data or []
    if not rows:
        return None
    row = rows[0]
    return MatchResult(
        ingredient_id=UUID(row["ingredient_id"]),
        match_type=row["match_type"],
        confidence=float(row["confidence"]),
    )


@lru_cache(maxsize=1)
def remote_client() -> Client | None:
    s = settings()
    if not s.remote_supabase_url or not s.remote_supabase_publishable_key:
        return None
    return create_client(s.remote_supabase_url, s.remote_supabase_publishable_key)


def reset_remote_client() -> None:
    remote_client.cache_clear()
