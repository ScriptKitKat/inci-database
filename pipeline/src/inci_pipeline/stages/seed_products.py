"""Stage 7: seed products + decoded ingredient lists from OBF.

Streams the OBF dump (same input as stage 3) and persists each product
plus its tokenized + matched ingredient list. Position = label order.
"""

from __future__ import annotations

import logging
import hashlib
from datetime import datetime, timezone
from ..config import settings
from ..db import (
    client,
    fetch_exact_match_index,
    fetch_existing_product_slugs,
    ingestion_run,
    reset_client,
)
from ..normalize import normalize_brand_name, normalize_name, slug, tokenize_label
from ..sources.open_beauty_facts import stream

log = logging.getLogger(__name__)

STAGE = "products_seed"

_brand_id_cache: dict[str, str] = {}


def _canonical_brand(raw_brand: str | None) -> str | None:
    if not raw_brand:
        return None
    for part in raw_brand.replace(";", ",").split(","):
        brand = " ".join(part.split())
        if brand:
            return brand
    return None


def _product_slug(brand: str, product_name: str) -> str:
    return slug(f"{brand} {product_name}")


def _brand_slug(name: str, normalized: str) -> str:
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:6]
    return f"{slug(name) or 'brand'}-{digest}"


def _upsert_brand(name: str) -> str:
    normalized = normalize_brand_name(name)
    if normalized in _brand_id_cache:
        return _brand_id_cache[normalized]
    inserted = (
        client()
        .table("brands")
        .upsert(
            {
                "name": name,
                "slug": _brand_slug(name, normalized),
            },
            on_conflict="normalized",
        )
        .execute()
    )
    brand_id = inserted.data[0]["id"]
    _brand_id_cache[normalized] = brand_id
    return brand_id


def run(force: bool = False) -> None:
    s = settings()
    path = s.obf_dump_path
    if not path.exists():
        raise FileNotFoundError(f"OBF dump not found at {path}")

    match_index = fetch_exact_match_index()
    known_terms = set(match_index)
    log.info(
        "loaded %s normalized ingredient/alias terms for product tokenization", len(known_terms)
    )
    existing_product_slugs = fetch_existing_product_slugs()
    log.info("loaded %s existing product slugs for resume", len(existing_product_slugs))

    with ingestion_run(STAGE) as counters:
        for product in stream(path):
            brand = _canonical_brand(product.brand)
            if not product.name or not brand or not product.ingredients_text:
                continue
            tokens = tokenize_label(product.ingredients_text, known_terms=known_terms)
            if not tokens:
                continue
            counters["rows_in"] += 1

            product_slug = _product_slug(brand, product.name)
            if product_slug in existing_product_slugs:
                continue

            resolved_ingredients = [
                (position, match_index.get(normalize_name(token)))
                for position, token in enumerate(tokens, start=1)
            ]
            if any(ingredient_id is None for _, ingredient_id in resolved_ingredients):
                log.info(
                    "skipping product with ingredients that require review: %s / %s",
                    brand,
                    product.name,
                )
                continue

            brand_id = _upsert_brand(brand)
            inserted = (
                client()
                .table("products")
                .upsert(
                    {
                        "name": product.name,
                        "slug": product_slug,
                        "brand_id": brand_id,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    on_conflict="slug",
                )
                .execute()
            )
            product_id = inserted.data[0]["id"]

            rows = [
                {
                    "product_id": product_id,
                    "position": position,
                    "ingredient_id": str(ingredient_id),
                }
                for position, ingredient_id in resolved_ingredients
            ]
            if rows:
                client().table("product_ingredients").delete().eq(
                    "product_id", product_id
                ).execute()
                client().table("product_ingredients").insert(rows).execute()
                counters["rows_upserted"] += len(rows)
                existing_product_slugs.add(product_slug)
                if len(existing_product_slugs) % 500 == 0:
                    log.info("imported/resumed through %s products", len(existing_product_slugs))
                    reset_client()
