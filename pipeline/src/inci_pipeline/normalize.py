"""String normalization. Mirrors the Postgres `normalized_name`
generated column so Python matching produces identical results.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable

from slugify import slugify as _slugify

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_WHITESPACE = re.compile(r"\s+")

# Common label-text tokens that aren't real ingredients.
_LABEL_NOISE = {
    "ingredients",
    "ingrediants",
    "and",
    "may contain",
    "ci",
    "and or",
}


def normalize_name(text: str) -> str:
    """Lowercase, strip accents, drop punctuation. Mirrors the SQL
    generated column expression so matching is symmetric."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = _NON_ALNUM.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def slug(inci_name: str) -> str:
    """URL slug for an ingredient (e.g. 'Salicylic Acid' -> 'salicylic-acid').

    No max_length: some real INCI names (fermentation lysates,
    multi-organism complexes) share long prefixes and truncating to a
    fixed length causes collisions with the UNIQUE constraint.
    Callers that need collision-proofing on top of this should use
    `slug_with_fallback`.
    """
    return _slugify(inci_name)


def slug_with_fallback(inci_name: str, seen_slugs: set[str]) -> str:
    """Return a unique slug for `inci_name`, mutating `seen_slugs`.

    If the natural slug is already taken, suffix with a 6-char SHA-1 of
    the INCI name so the result stays stable across re-runs (the hash
    is deterministic in `inci_name`).
    """
    base = slug(inci_name)
    candidate = base
    if candidate in seen_slugs:
        digest = hashlib.sha1(inci_name.encode("utf-8")).hexdigest()[:6]
        candidate = f"{base}-{digest}"
    seen_slugs.add(candidate)
    return candidate


def tokenize_label(label: str) -> list[str]:
    """Split a raw ingredient list from a product label into tokens.

    Handles common separators (comma, semicolon), parenthetical
    concentrations ('Aqua (Water 99%)' -> 'Aqua' + 'Water 99%'),
    and strips obvious label noise.
    """
    if not label:
        return []
    # Replace bullet-y separators with commas
    label = label.replace("·", ",").replace("•", ",").replace(";", ",")
    parts = []
    for chunk in label.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Split parenthetical content out as its own token
        depth = 0
        buf = []
        for ch in chunk:
            if ch == "(":
                if buf:
                    parts.append("".join(buf).strip())
                    buf = []
                depth += 1
            elif ch == ")":
                if buf:
                    parts.append("".join(buf).strip())
                    buf = []
                depth = max(0, depth - 1)
            else:
                buf.append(ch)
        if buf:
            parts.append("".join(buf).strip())
    return [p for p in (s.strip() for s in parts) if p and normalize_name(p) not in _LABEL_NOISE]


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out
