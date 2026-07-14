"""Stage 6: classify skin_type_tag and concern_tag.

Heuristic-first: derive from CosIng function_tags + abstract keywords
when possible. Only call Claude (Sonnet) when no heuristic match exists.
Rating remains NULL — that field is reserved for human curators.
"""

from __future__ import annotations

import logging

from ..db import client, ingestion_run

log = logging.getLogger(__name__)

STAGE = "classify_tags"

# Minimal seed mapping for the heuristic pass. Extend as the team
# learns which CosIng function strings cluster with which skin types.
_FUNCTION_TO_SKIN_TYPE = {
    "humectant": ["dry", "all"],
    "emollient": ["dry", "all"],
    "exfoliating": ["oily", "acne_prone"],
    "antioxidant": ["all"],
    "skin_conditioning": ["all"],
    "skin_protecting": ["sensitive", "all"],
}
_FUNCTION_TO_CONCERN = {
    "exfoliating": ["acne", "texture"],
    "antioxidant": ["aging"],
    "skin_lightening": ["hyperpigmentation"],
    "uv_filter": ["aging"],
    "anti_seborrheic": ["acne"],
}


def run(force: bool = False) -> None:
    with ingestion_run(STAGE) as counters:
        offset = 0
        page = 500
        while True:
            res = (
                client()
                .table("ingredient_information")
                .select("ingredient_id, functions, additional_information")
                .range(offset, offset + page - 1)
                .execute()
            )
            rows = res.data or []
            if not rows:
                return
            for row in rows:
                counters["rows_in"] += 1
                skin_types, concerns = _classify(row.get("functions") or [])
                additional = row.get("additional_information") or {}
                # Only write if we have something the row doesn't already.
                update = {}
                if skin_types and not additional.get("skin_type_tags"):
                    update["skin_type_tags"] = skin_types
                if concerns and not additional.get("concern_tags"):
                    update["concern_tags"] = concerns
                if update:
                    client().table("ingredient_information").update(
                        {"additional_information": {**additional, **update}}
                    ).eq(
                        "ingredient_id", row["ingredient_id"]
                    ).execute()
                    counters["rows_upserted"] += 1
            if len(rows) < page:
                return
            offset += page


def _classify(function_tags: list[str]) -> tuple[list[str], list[str]]:
    skin_types: set[str] = set()
    concerns: set[str] = set()
    for fn in function_tags:
        skin_types.update(_FUNCTION_TO_SKIN_TYPE.get(fn, []))
        concerns.update(_FUNCTION_TO_CONCERN.get(fn, []))
    return sorted(skin_types), sorted(concerns)
