"""Stage 3: harvest label-variant aliases from Open Beauty Facts.

Streams the OBF bulk JSONL dump, tokenizes each product's
ingredients_text, matches each token against the existing alias index,
and inserts new aliases for tokens that resolve confidently but are
not yet recorded.

Unmatched tokens land in `data/unmatched_tokens.csv` for human review.
"""

from __future__ import annotations

import csv
import logging
from collections import Counter
from pathlib import Path

from ..config import settings
from ..db import AliasRow, ingestion_run, upsert_aliases
from ..matching.match import match_token
from ..normalize import normalize_name, tokenize_label
from ..sources.open_beauty_facts import stream

log = logging.getLogger(__name__)

STAGE = "obf_aliases"


def run(force: bool = False) -> None:
    s = settings()
    path = s.obf_dump_path
    if not path.exists():
        raise FileNotFoundError(
            f"OBF dump not found at {path}. Download "
            f"openbeautyfacts-products.jsonl.gz from "
            f"world.openbeautyfacts.org/data and place it there."
        )

    threshold = s.obf_match_threshold
    unmatched_counter: Counter[str] = Counter()
    seen_aliases: set[tuple[str, str]] = set()
    alias_batch: list[AliasRow] = []

    with ingestion_run(STAGE, metadata={"threshold": threshold}) as counters:
        for product in stream(path):
            if not product.ingredients_text:
                continue
            for token in tokenize_label(product.ingredients_text):
                counters["rows_in"] += 1
                normalized = normalize_name(token)
                if not normalized:
                    continue
                hit = match_token(token)
                if hit is None or hit.confidence < threshold:
                    unmatched_counter[normalized] += 1
                    continue
                key = (str(hit.ingredient_id), normalized)
                if key in seen_aliases:
                    continue
                seen_aliases.add(key)
                alias_batch.append(
                    AliasRow(
                        ingredient_id=hit.ingredient_id,
                        alias=token,
                        alias_type="common",
                        source="open_beauty_facts",
                    )
                )
                if len(alias_batch) >= 1000:
                    counters["rows_upserted"] += upsert_aliases(alias_batch)
                    alias_batch.clear()

        if alias_batch:
            counters["rows_upserted"] += upsert_aliases(alias_batch)

    _dump_unmatched(unmatched_counter)


def _dump_unmatched(counter: Counter[str], limit: int = 5000) -> None:
    out = Path("data/unmatched_tokens.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["token", "count"])
        for token, count in counter.most_common(limit):
            w.writerow([token, count])
    log.info("wrote %d unmatched tokens to %s", min(limit, len(counter)), out)
