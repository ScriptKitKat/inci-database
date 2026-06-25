"""Token -> ingredient resolver.

Exact and alias hits are resolved in-memory from a preloaded index.
Only tokens that miss locally are sent to Postgres for fuzzy matching.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from postgrest.exceptions import APIError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ..db import client
from ..normalize import normalize_name

log = logging.getLogger(__name__)

FUZZY_BATCH_SIZE = 8
_PAGE = 1000


@dataclass(frozen=True)
class MatchResult:
    ingredient_id: UUID
    match_type: str
    confidence: float


class MatchIndex:
    """Preloaded canonical + alias maps for O(1) exact matching."""

    __slots__ = ("canonical", "alias")

    def __init__(self) -> None:
        self.canonical: dict[str, UUID] = {}
        self.alias: dict[str, UUID] = {}

    @classmethod
    def load(cls) -> MatchIndex:
        idx = cls()
        offset = 0
        while True:
            res = (
                client()
                .table("ingredients")
                .select("id, normalized_name")
                .range(offset, offset + _PAGE - 1)
                .execute()
            )
            rows = res.data or []
            if not rows:
                break
            for row in rows:
                idx.canonical[row["normalized_name"]] = UUID(row["id"])
            if len(rows) < _PAGE:
                break
            offset += _PAGE

        offset = 0
        while True:
            res = (
                client()
                .table("ingredient_aliases")
                .select("ingredient_id, normalized_alias")
                .range(offset, offset + _PAGE - 1)
                .execute()
            )
            rows = res.data or []
            if not rows:
                break
            for row in rows:
                norm = row["normalized_alias"]
                if norm not in idx.alias:
                    idx.alias[norm] = UUID(row["ingredient_id"])
            if len(rows) < _PAGE:
                break
            offset += _PAGE

        log.info(
            "match index loaded: %d canonical, %d aliases",
            len(idx.canonical),
            len(idx.alias),
        )
        return idx

    def exact(self, token: str) -> MatchResult | None:
        norm = normalize_name(token)
        if not norm:
            return None
        if norm in self.canonical:
            return MatchResult(self.canonical[norm], "canonical_exact", 1.0)
        if norm in self.alias:
            return MatchResult(self.alias[norm], "alias_exact", 0.98)
        return None


class _CacheMiss:
    pass


_CACHE_MISS = _CacheMiss()


class TokenMatchCache:
    """Caches token results; exact hits never touch the network."""

    __slots__ = ("_index", "_fuzzy", "_hits", "_misses")

    def __init__(self, index: MatchIndex, *, fuzzy: bool = False) -> None:
        self._index = index
        self._fuzzy = fuzzy
        self._hits: dict[str, MatchResult] = {}
        self._misses: set[str] = set()

    @property
    def size(self) -> int:
        return len(self._hits) + len(self._misses)

    def resolve_many(self, tokens: list[str]) -> dict[str, MatchResult | None]:
        out: dict[str, MatchResult | None] = {}
        fuzzy_pending: list[str] = []

        for token in tokens:
            if not token or not token.strip():
                continue
            if token in self._hits:
                out[token] = self._hits[token]
                continue
            if token in self._misses:
                out[token] = None
                continue

            hit = self._index.exact(token)
            if hit:
                self._hits[token] = hit
                out[token] = hit
            else:
                fuzzy_pending.append(token)

        if not self._fuzzy:
            for token in fuzzy_pending:
                self._misses.add(token)
                out[token] = None
            return out

        for i in range(0, len(fuzzy_pending), FUZZY_BATCH_SIZE):
            batch = fuzzy_pending[i : i + FUZZY_BATCH_SIZE]
            try:
                batch_hits = _match_batch_rpc(batch)
            except APIError:
                batch_hits = {token: None for token in batch}
            for token, hit in batch_hits.items():
                if hit:
                    self._hits[token] = hit
                else:
                    self._misses.add(token)
                out[token] = hit
        return out


def _is_transient_match_error(exc: BaseException) -> bool:
    if not isinstance(exc, APIError):
        return False
    code = exc.code or (exc.args[0].get("code") if exc.args else None)
    return code in ("57014", "PGRST003")


def _row_to_result(row: dict) -> MatchResult:
    return MatchResult(
        ingredient_id=UUID(row["ingredient_id"]),
        match_type=row["match_type"],
        confidence=float(row["confidence"]),
    )


@retry(
    retry=retry_if_exception(_is_transient_match_error),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _match_batch_rpc(tokens: list[str]) -> dict[str, MatchResult | None]:
    if not tokens:
        return {}
    res = client().rpc("match_ingredients_batch", {"inputs": tokens}).execute()
    hits: dict[str, MatchResult] = {}
    for row in res.data or []:
        token = row["input_token"]
        if token not in hits:
            hits[token] = _row_to_result(row)
    return {token: hits.get(token) for token in tokens}


@retry(
    retry=retry_if_exception(_is_transient_match_error),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _match_rpc(token: str):
    return client().rpc("match_ingredient", {"input": token}).execute()


def match_token(
    token: str,
    cache: TokenMatchCache | None = None,
) -> MatchResult | None:
    if not token or not token.strip():
        return None
    if cache is not None:
        return cache.resolve_many([token]).get(token)
    res = _match_rpc(token)
    rows = res.data or []
    if not rows:
        return None
    return _row_to_result(rows[0])
