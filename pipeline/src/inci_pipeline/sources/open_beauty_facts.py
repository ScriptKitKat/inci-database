"""Stream the Open Beauty Facts bulk JSONL dump.

OBF publishes a gzipped JSONL dump at world.openbeautyfacts.org/data.
Each line is a product. We yield (barcode, name, brand, ingredients_text)
so the harvester can tokenize ingredients_text against our alias index.
"""

from __future__ import annotations

import gzip
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import orjson


@dataclass(frozen=True)
class OBFProduct:
    barcode: str
    name: str | None
    brand: str | None
    ingredients_text: str | None


def stream(path: Path) -> Iterator[OBFProduct]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = orjson.loads(line)
            except orjson.JSONDecodeError:
                continue
            barcode = rec.get("code") or rec.get("_id")
            if not barcode:
                continue
            yield OBFProduct(
                barcode=str(barcode),
                name=rec.get("product_name"),
                brand=rec.get("brands"),
                ingredients_text=rec.get("ingredients_text_en")
                or rec.get("ingredients_text"),
            )
