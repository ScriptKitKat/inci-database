"""Stage 1b: enrich ingredients with Wikidata data via SPARQL.

For each ingredient that has a CAS number, look up the matching
Wikidata item and fill in EC number (if missing) plus record the
Wikidata item URI and any InChI / chemical formula in
`ingredient_sources` for later use.

Batches CAS numbers per query (default 40) to stay well under the
Wikidata Query Service's 60-second timeout.
"""

from __future__ import annotations

import logging
from uuid import UUID

from ..db import SourceRow, client, ingestion_run, stream_ingredients_with_cas, upsert_sources
from ..sources.wikidata import WikidataClient, chunked

log = logging.getLogger(__name__)

STAGE = "wikidata_enrich"
BATCH = 40


def run(force: bool = False) -> None:
    cas_to_ingredient: dict[str, tuple[UUID, str | None]] = {}
    for row in stream_ingredients_with_cas():
        cas = row.get("cas_number")
        if not cas:
            continue
        cas_to_ingredient[cas] = (UUID(row["id"]), row.get("ec_number"))

    cas_numbers = list(cas_to_ingredient.keys())
    log.info("looking up %d CAS numbers on Wikidata", len(cas_numbers))

    with ingestion_run(STAGE) as counters, WikidataClient() as wd:
        counters["rows_in"] = len(cas_numbers)
        source_batch: list[SourceRow] = []

        for batch in chunked(cas_numbers, BATCH):
            try:
                records = wd.lookup_by_cas(batch)
            except Exception as exc:
                log.warning("wikidata batch failed: %s", exc)
                continue

            for record in records:
                entry = cas_to_ingredient.get(record.cas)
                if entry is None:
                    continue
                ing_id, existing_ec = entry

                update: dict = {}
                if record.ec and not existing_ec:
                    update["ec_number"] = record.ec
                if update:
                    client().table("ingredients").update(update).eq(
                        "id", str(ing_id)
                    ).execute()
                    counters["rows_upserted"] += 1

                source_batch.append(
                    SourceRow(
                        ingredient_id=ing_id,
                        source_type="wikidata",
                        external_id=record.item_uri.rsplit("/", 1)[-1],
                        url=record.item_uri,
                        raw_payload={
                            "ec": record.ec,
                            "inchi": record.inchi,
                            "formula": record.formula,
                        },
                    )
                )
            if len(source_batch) >= 500:
                upsert_sources(source_batch)
                source_batch.clear()

        if source_batch:
            upsert_sources(source_batch)
