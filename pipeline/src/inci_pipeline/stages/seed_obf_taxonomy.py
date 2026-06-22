"""Stage 1: seed `ingredients` from the OBF ingredients taxonomy.

Replaces the original CosIng seed because CosIng no longer offers a
bulk download. OBF's taxonomy file is plain text, mirrored on GitHub,
and already deduped + canonicalized. Other-language canonical names
become `translation` aliases; English synonyms become `synonym`
aliases. CAS, EC, Wikidata ID, and PubChem CID are stored on the row
when present.
"""

from __future__ import annotations

import logging

from ..config import settings
from ..db import (
    AliasRow,
    IngredientRow,
    SourceRow,
    ingestion_run,
    upsert_aliases,
    upsert_ingredients,
    upsert_sources,
)
from ..normalize import normalize_name, slug_with_fallback
from ..sources import obf_taxonomy

log = logging.getLogger(__name__)

STAGE = "obf_taxonomy_seed"


def run(force: bool = False) -> None:
    s = settings()
    path = s.obf_taxonomy_path
    if not path.exists():
        raise FileNotFoundError(
            f"OBF ingredients taxonomy not found at {path}. Download from "
            f"https://raw.githubusercontent.com/openfoodfacts/openbeautyfacts-server/main/taxonomies/ingredients.txt"
        )

    with ingestion_run(STAGE, metadata={"file": str(path)}) as counters:
        ingredient_rows: list[IngredientRow] = []
        # We need ingredient_id (after upsert) before we can insert
        # aliases and sources, so we materialise the parse first.
        parsed = list(obf_taxonomy.parse(path))

        # Dedupe by normalized_name (lower + unaccent + strip punctuation)
        # to match the SQL generated column. Otherwise 'water', 'WATER',
        # and 'Aqua' all reach the upsert as separate rows and violate
        # the UNIQUE constraint on normalized_name.
        seen_names: set[str] = set()
        seen_slugs: set[str] = set()
        for entry in parsed:
            counters["rows_in"] += 1
            canonical_key = normalize_name(entry.en_canonical)
            if not canonical_key or canonical_key in seen_names:
                continue
            seen_names.add(canonical_key)
            ingredient_rows.append(
                IngredientRow(
                    inci_name=entry.en_canonical,
                    slug=slug_with_fallback(entry.en_canonical, seen_slugs),
                    cas_number=entry.cas_number,
                    ec_number=entry.ec_number,
                )
            )

        log.info("upserting %d ingredients from OBF taxonomy", len(ingredient_rows))
        id_map = upsert_ingredients(ingredient_rows)
        counters["rows_upserted"] = len(id_map)
        log.info("got %d ingredient ids back from upsert", len(id_map))

        # OBF entries occasionally repeat a synonym, list the canonical
        # name in the synonym slot, or reference the same Wikidata item
        # twice. Dedupe by the upsert conflict key to avoid PostgreSQL's
        # "ON CONFLICT DO UPDATE command cannot affect row a second time".
        alias_rows: list[AliasRow] = []
        source_rows: list[SourceRow] = []
        alias_seen: set[tuple[str, str, str]] = set()
        source_seen: set[tuple[str, str, str]] = set()

        for entry in parsed:
            ing_id = id_map.get(entry.en_canonical)
            if ing_id is None:
                continue
            ing_key = str(ing_id)
            canonical = entry.en_canonical

            for syn in entry.en_synonyms:
                if not syn or syn == canonical:
                    continue
                key = (ing_key, syn, "en")
                if key in alias_seen:
                    continue
                alias_seen.add(key)
                alias_rows.append(
                    AliasRow(
                        ingredient_id=ing_id,
                        alias=syn,
                        alias_type="synonym",
                        language="en",
                        source="open_beauty_facts",
                    )
                )

            for lang, names in entry.other_lang_names.items():
                for name in names:
                    if not name:
                        continue
                    key = (ing_key, name, lang)
                    if key in alias_seen:
                        continue
                    alias_seen.add(key)
                    alias_rows.append(
                        AliasRow(
                            ingredient_id=ing_id,
                            alias=name,
                            alias_type="translation",
                            language=lang,
                            source="open_beauty_facts",
                        )
                    )

            if entry.wikidata_id:
                source_key = (ing_key, "wikidata", entry.wikidata_id)
                if source_key not in source_seen:
                    source_seen.add(source_key)
                    source_rows.append(
                        SourceRow(
                            ingredient_id=ing_id,
                            source_type="wikidata",
                            external_id=entry.wikidata_id,
                            url=f"https://www.wikidata.org/wiki/{entry.wikidata_id}",
                            raw_payload={"source": "obf_taxonomy"},
                        )
                    )

        log.info("upserting %d aliases, %d source rows", len(alias_rows), len(source_rows))
        upsert_aliases(alias_rows)
        upsert_sources(source_rows)
