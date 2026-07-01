"""Stage 7: seed products + decoded ingredient lists from OBF.

Streams the OBF dump (same input as stage 3) and persists each product
plus its tokenized + matched ingredient list. Position = label order.
"""

from __future__ import annotations

import logging
import hashlib
from datetime import datetime, timezone

from ..config import settings
from ..db import client, fetch_exact_match_index, fetch_existing_product_slugs, ingestion_run, reset_client
from ..normalize import ingredient_fingerprint, normalize_brand_name, normalize_name, slug, tokenize_label
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


def _fingerprint_collision_id(fingerprint: str, product_slug: str) -> str | None:
    existing = (
        client()
        .table("products")
        .select("id, slug")
        .eq("ingredient_fingerprint", fingerprint)
        .limit(1)
        .execute()
    )
    if not existing.data:
        return None
    row = existing.data[0]
    if row["slug"] == product_slug:
        return None
    return row["id"]


def run(force: bool = False) -> None:
    s = settings()
    path = s.obf_dump_path
    if not path.exists():
        raise FileNotFoundError(f"OBF dump not found at {path}")

    match_index = fetch_exact_match_index()
    known_terms = set(match_index)
    log.info("loaded %s normalized ingredient/alias terms for product tokenization", len(known_terms))
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
            fingerprint = ingredient_fingerprint(tokens)
            if _fingerprint_collision_id(fingerprint, product_slug):
                log.info(
                    "skipping probable duplicate product with fingerprint collision: %s / %s",
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
                        "ingredient_fingerprint": fingerprint,
                        "status": "approved",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    on_conflict="slug",
                )
                .execute()
            )
            product_id = inserted.data[0]["id"]

            rows = []
            for position, token in enumerate(tokens, start=1):
                ingredient_id = match_index.get(normalize_name(token))
                rows.append(
                    {
                        "product_id": product_id,
                        "position": position,
                        "raw_inci_token": token,
                        "ingredient_id": str(ingredient_id) if ingredient_id else None,
                        "is_matched": ingredient_id is not None,
                    }
                )
            if rows:
                client().table("product_ingredients").delete().eq("product_id", product_id).execute()
                client().table("product_ingredients").upsert(rows).execute()
                counters["rows_upserted"] += len(rows)
                existing_product_slugs.add(product_slug)
                if len(existing_product_slugs) % 500 == 0:
                    log.info("imported/resumed through %s products", len(existing_product_slugs))
                    reset_client()
