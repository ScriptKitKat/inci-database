"""Export editorial prompts to disk for the manual paste workflow.

For each curated ingredient that has at least one PubMed source row,
writes `<slug>.prompt.md` to the inbox dir. The user pastes that
file into Claude.ai or ChatGPT and saves the JSON response as
`<slug>.json` in the same folder, then runs `import-editorial`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from ..db import _fetch_curated_ids, client, fetch_ingredients_for_editorial
from ..llm.claude import build_editorial_prompt
from ..normalize import slug as slugify

log = logging.getLogger(__name__)

INSTRUCTIONS = """\
# Editorial prompt for: {inci_name}

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `{slug}.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

"""


def run(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = _fetch_curated_ids()
    if not ids:
        log.warning("curation queue is empty; nothing to export")
        return

    written = 0
    skipped_no_abstracts: list[str] = []
    for row in fetch_ingredients_for_editorial(ids):
        ing_id = UUID(row["id"])
        abstracts = _fetch_abstracts(ing_id)
        if not abstracts:
            skipped_no_abstracts.append(row["inci_name"])
            continue
        prompt = build_editorial_prompt(
            inci_name=row["inci_name"],
            function_tags=row.get("function_tags") or [],
            is_restricted_eu=row.get("is_restricted_eu", False),
            is_restricted_us=row.get("is_restricted_us", False),
            abstracts=abstracts,
        )
        slug = slugify(row["inci_name"])
        path = out_dir / f"{slug}.prompt.md"
        path.write_text(
            INSTRUCTIONS.format(inci_name=row["inci_name"], slug=slug) + prompt,
            encoding="utf-8",
        )
        written += 1

    log.info("wrote %d prompts to %s", written, out_dir)
    if skipped_no_abstracts:
        log.info(
            "skipped %d ingredients with no PubMed sources yet "
            "(run `make pubmed` first): %s",
            len(skipped_no_abstracts),
            ", ".join(skipped_no_abstracts[:10]) + (
                "..." if len(skipped_no_abstracts) > 10 else ""
            ),
        )


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
