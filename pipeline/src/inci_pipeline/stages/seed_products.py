"""Stage 7: seed products + decoded ingredient lists from OBF.

Streams the OBF dump (same input as stage 3) and persists each product
plus its tokenized + matched ingredient list. Position = label order.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from ..config import settings
from ..db import client, ingestion_run
from ..matching.match import match_token
from ..normalize import tokenize_label
from ..sources.open_beauty_facts import stream

log = logging.getLogger(__name__)

STAGE = "products_seed"


def run(force: bool = False) -> None:
    s = settings()
    path = s.obf_dump_path
    if not path.exists():
        raise FileNotFoundError(f"OBF dump not found at {path}")

    with ingestion_run(STAGE) as counters:
        for product in stream(path):
            if not product.name or not product.ingredients_text:
                continue
            counters["rows_in"] += 1

            inserted = (
                client()
                .table("products")
                .upsert(
                    {
                        "external_id": product.barcode,
                        "external_source": "open_beauty_facts",
                        "name": product.name,
                        "brand": product.brand,
                        "raw_ingredients": product.ingredients_text,
                        "decoded_at": datetime.now(timezone.utc).isoformat(),
                    },
                    on_conflict="external_source,external_id",
                )
                .execute()
            )
            product_id = inserted.data[0]["id"]

            rows = []
            for position, token in enumerate(tokenize_label(product.ingredients_text), start=1):
                hit = match_token(token)
                rows.append(
                    {
                        "product_id": product_id,
                        "position": position,
                        "raw_token": token,
                        "ingredient_id": str(hit.ingredient_id) if hit else None,
                        "match_confidence": hit.confidence if hit else None,
                    }
                )
            if rows:
                client().table("product_ingredients").upsert(rows).execute()
                counters["rows_upserted"] += len(rows)
