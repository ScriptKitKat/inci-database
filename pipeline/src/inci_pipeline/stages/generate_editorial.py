"""Stage 5: generate editorial summaries with Claude.

For each ingredient with PubMed sources, assemble {inci_name, function
tags, restrictions, abstracts} and prompt Claude for structured JSON.
Upserts `ingredient_content` with status='draft' and a versioned
model_version. Human curators flip status to 'published' separately.

Rating is intentionally never written by this stage.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from ..db import (
    _fetch_curated_ids,
    client,
    fetch_ingredients_for_editorial,
    ingestion_run,
)
from ..llm.claude import EDITORIAL_MODEL, generate_editorial

log = logging.getLogger(__name__)

STAGE = "editorial_generate"
BATCH = 50


def run(force: bool = False, process_all: bool = False) -> None:
    model_version = f"{EDITORIAL_MODEL}@{date.today().isoformat()}"

    with ingestion_run(
        STAGE, metadata={"model": model_version, "curated_only": not process_all}
    ) as counters:
        rows_iter = _all_ingredients() if process_all else _curated_ingredients()
        for row in rows_iter:
            counters["rows_in"] += 1
            ing_id = UUID(row["id"])
            abstracts = _fetch_abstracts(ing_id)
            if not abstracts:
                log.info("skip %s: no PubMed sources yet", row["inci_name"])
                continue
            try:
                editorial = generate_editorial(
                    inci_name=row["inci_name"],
                    function_tags=row.get("function_tags") or [],
                    is_restricted_eu=row.get("is_restricted_eu", False),
                    is_restricted_us=row.get("is_restricted_us", False),
                    abstracts=abstracts,
                )
            except Exception as exc:
                log.warning("editorial failed for %s: %s", row["inci_name"], exc)
                continue

            client().table("ingredient_content").upsert(
                {
                    "ingredient_id": str(ing_id),
                    "language": "en",
                    "status": "draft",
                    "model_version": model_version,
                    "summary_short": editorial.summary_short,
                    "summary_long": editorial.summary_long,
                    "quick_facts": editorial.quick_facts,
                    "what_it_does": editorial.what_it_does,
                },
                on_conflict="ingredient_id,language",
            ).execute()
            counters["rows_upserted"] += 1


def _curated_ingredients():
    ids = _fetch_curated_ids()
    if not ids:
        log.warning("curation queue is empty; nothing to do")
        return
    yield from fetch_ingredients_for_editorial(ids)


def _all_ingredients():
    offset = 0
    while True:
        res = (
            client()
            .table("ingredients")
            .select("id, inci_name, function_tags, is_restricted_eu, is_restricted_us")
            .range(offset, offset + BATCH - 1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return
        yield from rows
        if len(rows) < BATCH:
            return
        offset += BATCH


def _fetch_abstracts(ingredient_id: UUID, limit: int = 5) -> list[dict]:
    res = (
        client()
        .table("ingredient_sources")
        .select("title, raw_payload")
        .eq("ingredient_id", str(ingredient_id))
        .eq("source_type", "pubmed")
        .limit(limit)
        .execute()
    )
    return res.data or []
