"""Stage 4: fetch top PubMed abstracts per ingredient.

For each ingredient, search PubMed by INCI name (and CAS when known),
fetch up to 5 abstracts, and insert them as `ingredient_sources` rows
with raw_payload = parsed abstract dict.
"""

from __future__ import annotations

import logging
import time
from uuid import UUID

from ..config import settings
from ..db import (
    SourceRow,
    ingestion_run,
    stream_curated_ingredients,
    stream_ingredients_with_cas,
    upsert_sources,
)
from ..sources.pubmed import PubMedClient

log = logging.getLogger(__name__)

STAGE = "pubmed_fetch"
MAX_ABSTRACTS = 5


def run(force: bool = False, process_all: bool = False) -> None:
    s = settings()
    rate_delay = 0.12 if s.ncbi_api_key else 0.34  # 10/sec with key, 3/sec without
    source_stream = (
        stream_ingredients_with_cas()
        if process_all
        else stream_curated_ingredients(require_cas=True)
    )

    with ingestion_run(STAGE, metadata={"curated_only": not process_all}) as counters, \
         PubMedClient(api_key=s.ncbi_api_key) as pm:
        source_batch: list[SourceRow] = []
        for row in source_stream:
            counters["rows_in"] += 1
            ing_id = UUID(row["id"])
            inci_name = row["inci_name"]
            cas = row["cas_number"]
            try:
                pmids = pm.search(inci_name, cas=cas, max_results=MAX_ABSTRACTS)
                time.sleep(rate_delay)
                abstracts = pm.fetch(pmids)
                time.sleep(rate_delay)
            except Exception as exc:
                log.warning("pubmed failed for %s: %s", inci_name, exc)
                continue

            for abstract in abstracts:
                source_batch.append(
                    SourceRow(
                        ingredient_id=ing_id,
                        source_type="pubmed",
                        external_id=abstract.pmid,
                        url=abstract.url,
                        title=abstract.title,
                        raw_payload={
                            "abstract": abstract.abstract,
                            "journal": abstract.journal,
                            "year": abstract.year,
                        },
                    )
                )
            if len(source_batch) >= 500:
                counters["rows_upserted"] += upsert_sources(source_batch)
                source_batch.clear()

        if source_batch:
            counters["rows_upserted"] += upsert_sources(source_batch)
