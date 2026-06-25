"""Stage 7: seed products + decoded ingredient lists from OBF.

Uses chunked upserts and batched ingredient matching so a full OBF import
finishes in hours instead of days.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from postgrest.exceptions import APIError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ..config import settings
from ..db import client, ingestion_run
from ..matching.match import MatchIndex, TokenMatchCache
from ..normalize import (
    first_brand,
    generate_fingerprint,
    normalize_brand,
    product_slug,
    slug_with_fallback,
    tokenize_label,
)
from ..sources.open_beauty_facts import OBFProduct, stream

log = logging.getLogger(__name__)

STAGE = "products_seed"
PRODUCT_CHUNK = 50


def _is_transient_db_error(exc: BaseException) -> bool:
    if isinstance(exc, APIError):
        code = exc.code or (exc.args[0].get("code") if exc.args else None)
        return code in ("57014", "PGRST003", "08006", "08003", "57P01")
    name = type(exc).__name__
    return name in {"ReadError", "ConnectError", "RemoteProtocolError", "WriteError"}


def _db_call(fn):
    @retry(
        retry=retry_if_exception(_is_transient_db_error),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    def wrapped():
        return fn()

    return wrapped()


@dataclass
class _ParsedProduct:
    obf: OBFProduct
    brand_name: str
    tokens: list[str]
    fingerprint: str


def _resolve_brand_id(brand_name: str, cache: dict[str, UUID], seen_slugs: set[str]) -> UUID:
    norm = normalize_brand(brand_name)
    if norm in cache:
        return cache[norm]

    existing = _db_call(
        lambda: client()
        .table("brands")
        .select("id")
        .eq("normalized", norm)
        .limit(1)
        .execute()
    )
    if existing.data:
        brand_id = UUID(existing.data[0]["id"])
        cache[norm] = brand_id
        return brand_id

    slug = slug_with_fallback(brand_name, seen_slugs)

    by_slug = _db_call(
        lambda: client()
        .table("brands")
        .select("id")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )
    if by_slug.data:
        brand_id = UUID(by_slug.data[0]["id"])
        cache[norm] = brand_id
        return brand_id

    res = _db_call(
        lambda: client()
        .table("brands")
        .upsert(
            {"name": brand_name.strip(), "slug": slug},
            on_conflict="slug",
        )
        .execute()
    )
    brand_id = UUID(res.data[0]["id"])
    cache[norm] = brand_id
    return brand_id


def _existing_fingerprint_slugs(fingerprints: list[str]) -> dict[str, str]:
    """Map ingredient_fingerprint -> slug for products already in the DB."""
    if not fingerprints:
        return {}
    found: dict[str, str] = {}
    chunk = 200
    for i in range(0, len(fingerprints), chunk):
        batch = fingerprints[i : i + chunk]
        res = _db_call(
            lambda b=batch: client()
            .table("products")
            .select("ingredient_fingerprint, slug")
            .in_("ingredient_fingerprint", b)
            .execute()
        )
        for row in res.data or []:
            found[row["ingredient_fingerprint"]] = row["slug"]
    return found


def _parse_product(product: OBFProduct) -> _ParsedProduct | None:
    brand_name = first_brand(product.brand)
    if not product.name or not product.ingredients_text or not brand_name:
        return None
    tokens = tokenize_label(product.ingredients_text)
    if not tokens:
        return None
    return _ParsedProduct(
        obf=product,
        brand_name=brand_name,
        tokens=tokens,
        fingerprint=generate_fingerprint(tokens),
    )


def _flush_chunk(
    parsed: list[_ParsedProduct],
    brand_cache: dict[str, UUID],
    seen_slugs: set[str],
    match_cache: TokenMatchCache,
    counters: dict[str, int],
) -> None:
    if not parsed:
        return

    counters["rows_in"] += len(parsed)

    fp_slugs = _existing_fingerprint_slugs([p.fingerprint for p in parsed])
    todo_by_slug: dict[str, tuple[_ParsedProduct, str]] = {}
    for p in parsed:
        slug = product_slug(p.brand_name, p.obf.name, seen_slugs)
        existing_slug = fp_slugs.get(p.fingerprint)
        if existing_slug and existing_slug != slug:
            continue
        fp_slugs[p.fingerprint] = slug
        todo_by_slug[slug] = (p, slug)
    todo = list(todo_by_slug.values())

    if not todo:
        return

    unique_tokens: list[str] = []
    seen: set[str] = set()
    for p, _slug in todo:
        for token in p.tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append(token)
    matches = match_cache.resolve_many(unique_tokens)

    product_rows = []
    slug_to_parsed: dict[str, _ParsedProduct] = {}
    for p, slug in todo:
        brand_id = _resolve_brand_id(p.brand_name, brand_cache, seen_slugs)
        product_rows.append(
            {
                "name": p.obf.name.strip(),
                "slug": slug,
                "brand_id": str(brand_id),
                "ingredient_fingerprint": p.fingerprint,
                "status": "approved",
            }
        )
        slug_to_parsed[slug] = p

    upserted = _db_call(
        lambda: client()
        .table("products")
        .upsert(product_rows, on_conflict="slug")
        .execute()
    )

    pi_rows = []
    for row in upserted.data or []:
        product_id = row["id"]
        p = slug_to_parsed[row["slug"]]
        for position, token in enumerate(p.tokens, start=1):
            hit = matches.get(token)
            pi_rows.append(
                {
                    "product_id": product_id,
                    "position": position,
                    "raw_inci_token": token,
                    "ingredient_id": str(hit.ingredient_id) if hit else None,
                    "is_matched": hit is not None,
                }
            )

    if pi_rows:
        chunk = 500
        for i in range(0, len(pi_rows), chunk):
            batch = pi_rows[i : i + chunk]
            _db_call(
                lambda b=batch: client()
                .table("product_ingredients")
                .upsert(b, on_conflict="product_id,position")
                .execute()
            )
            counters["rows_upserted"] += len(batch)


def run(force: bool = False) -> None:
    s = settings()
    path = s.obf_dump_path
    if not path.exists():
        raise FileNotFoundError(f"OBF dump not found at {path}")

    brand_cache: dict[str, UUID] = {}
    seen_slugs: set[str] = set()
    match_cache = TokenMatchCache(MatchIndex.load(), fuzzy=False)
    chunk: list[_ParsedProduct] = []

    with ingestion_run(STAGE) as counters:
        for product in stream(path):
            parsed = _parse_product(product)
            if not parsed:
                continue
            chunk.append(parsed)
            if len(chunk) >= PRODUCT_CHUNK:
                _flush_chunk(chunk, brand_cache, seen_slugs, match_cache, counters)
                chunk = []
                log.info(
                    "progress: %d products in, %d ingredient rows upserted, "
                    "%d unique tokens cached",
                    counters["rows_in"],
                    counters["rows_upserted"],
                    match_cache.size,
                )

        _flush_chunk(chunk, brand_cache, seen_slugs, match_cache, counters)
