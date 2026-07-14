"""Stage 2: enrich ingredients with PubChem data.

For every ingredient that has a CAS number, fetch the matching
PubChem compound, persist its IUPAC name onto `ingredients`, and add
each PubChem synonym to `ingredient_aliases` (source='pubchem').
"""

from __future__ import annotations

import logging
import time
from uuid import UUID

from ..db import (
    AliasRow,
    ingestion_run,
    patch_ingredient_information,
    stream_ingredients_with_cas,
    upsert_aliases,
)
from ..sources.pubchem import PubChemClient

log = logging.getLogger(__name__)

STAGE = "pubchem_enrich"
RATE_DELAY = 0.25  # ~4 req/sec, safely under PubChem's 5/sec cap


def run(force: bool = False) -> None:
    with ingestion_run(STAGE) as counters, PubChemClient() as pub:
        alias_batch: list[AliasRow] = []
        for row in stream_ingredients_with_cas():
            counters["rows_in"] += 1
            cas = row["cas_number"]
            ing_id = UUID(row["id"])
            try:
                record = pub.lookup_by_cas(cas)
            except Exception as exc:
                log.warning("pubchem lookup failed for %s (%s): %s", row["inci_name"], cas, exc)
                continue
            if record is None:
                continue

            if record.iupac_name:
                patch_ingredient_information(
                    ing_id, cosing={"iupac_name": record.iupac_name}
                )

            for syn in record.synonyms:
                alias_batch.append(
                    AliasRow(
                        ingredient_id=ing_id,
                        alias=syn,
                        alias_type="synonym",
                        source="pubchem",
                    )
                )
            if len(alias_batch) >= 1000:
                counters["rows_upserted"] += upsert_aliases(alias_batch)
                alias_batch.clear()
            time.sleep(RATE_DELAY)

        if alias_batch:
            counters["rows_upserted"] += upsert_aliases(alias_batch)
