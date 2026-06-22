"""Read JSON files produced by the manual paste workflow and upsert
them into ingredient_content. Companion to `export_editorial`.

Expected layout in the inbox dir:
    salicylic-acid.prompt.md   (original prompt)
    salicylic-acid.json        (JSON response, hand-pasted)

Processed JSON files are moved to `processed/` next to the inbox.
"""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

import orjson

from ..db import client, ingestion_run
from ..llm.claude import parse_editorial_response
from ..normalize import slug as slugify

log = logging.getLogger(__name__)

STAGE = "editorial_import"


def run(in_dir: Path, reviewer: str = "manual") -> None:
    if not in_dir.exists():
        log.error("inbox directory %s does not exist", in_dir)
        return

    processed_dir = in_dir / "processed"
    processed_dir.mkdir(exist_ok=True)

    json_files = sorted(in_dir.glob("*.json"))
    if not json_files:
        log.warning("no JSON files in %s", in_dir)
        return

    # Resolve slugs to ingredient ids in one shot.
    slugs = [p.stem for p in json_files]
    res = (
        client()
        .table("ingredients")
        .select("id, slug, inci_name")
        .in_("slug", slugs)
        .execute()
    )
    slug_to_id = {r["slug"]: (UUID(r["id"]), r["inci_name"]) for r in res.data or []}

    failures: list[tuple[str, str]] = []
    succeeded: list[str] = []

    with ingestion_run(STAGE, metadata={"reviewer": reviewer}) as counters:
        for path in json_files:
            counters["rows_in"] += 1
            slug = path.stem
            looked_up = slug_to_id.get(slug)
            if looked_up is None:
                failures.append((path.name, f"no ingredient with slug={slug}"))
                continue
            ing_id, inci_name = looked_up

            try:
                editorial = parse_editorial_response(path.read_text(encoding="utf-8"))
            except (KeyError, ValueError, orjson.JSONDecodeError) as exc:
                failures.append((path.name, f"parse error: {exc}"))
                continue

            client().table("ingredient_content").upsert(
                {
                    "ingredient_id": str(ing_id),
                    "language": "en",
                    "status": "draft",
                    "model_version": f"manual:{reviewer}",
                    "summary_short": editorial.summary_short,
                    "summary_long": editorial.summary_long,
                    "quick_facts": editorial.quick_facts,
                    "what_it_does": editorial.what_it_does,
                },
                on_conflict="ingredient_id,language",
            ).execute()
            counters["rows_upserted"] += 1
            succeeded.append(inci_name)

            path.rename(processed_dir / path.name)

    log.info("imported %d editorial drafts", len(succeeded))
    for name in succeeded:
        log.info("  ok: %s", name)
    if failures:
        log.warning("%d failures:", len(failures))
        for fname, reason in failures:
            log.warning("  %s -> %s", fname, reason)
