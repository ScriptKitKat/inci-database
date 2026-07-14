"""String normalization. Mirrors the Postgres `normalized_name`
generated column so Python matching produces identical results.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Collection, Iterable

from slugify import slugify as _slugify

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_WHITESPACE = re.compile(r"\s+")
_LABEL_PREFIX = re.compile(
    r"^\s*(?:ingredients?|ngredients?|ingrediants?|inci)\b\s*[:\-]?\s*",
    re.IGNORECASE,
)
_INGREDIENT_MARKER = re.compile(
    r"\b(?:ingredients?|ngredients?|ingrediants?|inci)\b\s*[:\-]?\s*",
    re.IGNORECASE,
)
_NON_INGREDIENT_PREFIX = re.compile(
    r"^\s*(?:directions?|instructions?|how\s+to\s+use|usage|uso|modo\s+de\s+empleo|mode\s+d'emploi|"
    r"warnings?|cautions?|precautions?|lot|batch|mfg|manufacturing|exp|expiry)\b",
    re.IGNORECASE,
)
_NON_INGREDIENT_TAIL = re.compile(
    r"\b(?:directions?|instructions?|how\s+to\s+use|usage|uso|modo\s+de\s+empleo|mode\s+d'emploi|"
    r"warnings?|cautions?|precautions?|for\s+external\s+use\s+only|avoid\s+contact\s+with\s+eyes)\b.*$",
    re.IGNORECASE | re.DOTALL,
)
_MAY_CONTAIN = re.compile(
    r"\b(?:may\s+contain|peut\s+contenir|may\s+contain/peut\s+contenir)\b.*$",
    re.IGNORECASE | re.DOTALL,
)
_HAS_SEPARATOR = re.compile(r"[,;·•\n]")
_TOKEN_WORD = re.compile(r"[A-Za-z0-9]+(?:[/-][A-Za-z0-9]+)*")

# Common label-text tokens that aren't real ingredients.
_LABEL_NOISE = {
    "ingredients",
    "ingredient",
    "ngredients",
    "ingrediants",
    "and",
    "may contain",
    "may",
    "contain",
    "peut",
    "contenir",
    "de",
    "fil",
    "no",
    "beneficios",
    "consideraciones",
    "ci",
    "and or",
}

_COMMA_SPLIT_REPAIR_SUFFIXES = {
    "butter",
    "extract",
    "ferment",
    "juice",
    "oil",
    "powder",
    "wax",
    "water",
}

_COMMA_SPLIT_REPAIR_SUFFIX_PHRASES = {
    *_COMMA_SPLIT_REPAIR_SUFFIXES,
    "bark extract",
    "flower extract",
    "fruit extract",
    "kernel oil",
    "leaf extract",
    "leaf juice",
    "peel extract",
    "peel oil",
    "root extract",
    "seed butter",
    "seed extract",
    "seed oil",
    "seed powder",
}

_COMMA_SPLIT_REPAIR_ENDINGS = {
    "bark",
    "flower",
    "fruit",
    "kernel",
    "leaf",
    "root",
    "seed",
    "stem",
}

# Small fallback lexicon for labels that are all-caps and omit commas.
# The importer passes the full ingredient + alias index for broader coverage.
_COMMON_SPACE_DELIMITED_INGREDIENTS = {
    "aqua",
    "aquawater",
    "aquawatereau",
    "ascorbic acid",
    "acrylatesc1030 alkyl acrylate crosspolymer",
    "aloe barbadensis leaf juice",
    "benzyl alcohol",
    "bisethylhexyloxyphenol methoxyphenyl triazine",
    "butylene glycol",
    "caprylic capric triglyceride",
    "capryliccapric triglyceride",
    "carbomer",
    "c1215 alkyl benzoate",
    "cetearyl alcohol",
    "cetyl alcohol",
    "citric acid",
    "coco glucoside",
    "dimethicone",
    "disodium edta",
    "ethylhexylglycerin",
    "glycerin",
    "glycolic acid",
    "hyaluronic acid",
    "lactic acid",
    "niacinamide",
    "panthenol",
    "peg40 hydrogenated castor oil",
    "phenoxyethanol",
    "pentaerythrityl tetraditbutyl hydroxyhydrocinnamate",
    "potassium sorbate",
    "salicylic acid",
    "sodium benzoate",
    "sodium chloride",
    "sodium hyaluronate",
    "sodium hydroxide",
    "stearic acid",
    "shea butter",
    "tocopherol",
    "water",
    "xanthan gum",
}


def normalize_name(text: str) -> str:
    """Lowercase, strip accents, drop punctuation. Mirrors the SQL
    generated column expression so matching is symmetric."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = _NON_ALNUM.sub("", text)
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


def normalize_brand_name(name: str | None) -> str:
    """Normalize a product brand for deterministic brand de-duping."""
    if not name:
        return ""
    return _WHITESPACE.sub(" ", name.strip()).upper()


def ingredient_fingerprint(ingredient_tokens: Iterable[str]) -> str:
    """Hash a cleaned, ordered ingredient list for probable product de-duping."""
    normalized = [t.strip().upper() for t in ingredient_tokens if t.strip()]
    combined = "|".join(normalized)
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


def _strip_label_prefix(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = _LABEL_PREFIX.sub("", text)
    return text


def _extract_ingredient_section(text: str) -> str:
    ingredient_marker = _INGREDIENT_MARKER.search(text)
    if ingredient_marker and (
        ingredient_marker.start() == 0 or _NON_INGREDIENT_PREFIX.match(text)
    ):
        text = text[ingredient_marker.start() :]
    elif _NON_INGREDIENT_PREFIX.match(text):
        return ""
    return _NON_INGREDIENT_TAIL.sub("", text)


def _strip_may_contain_section(text: str) -> str:
    return _MAY_CONTAIN.sub("", text)


def _clean_token(token: str) -> str:
    token = _strip_label_prefix(token.strip())
    token = token.strip(" \t\r\n:.-")
    token = _WHITESPACE.sub(" ", token)
    return token


def _is_noise_token(token: str) -> bool:
    normalized = normalize_name(token)
    return (
        not normalized
        or normalized in _LABEL_NOISE
        or (len(normalized) == 1 and normalized.isalpha())
    )


def _looks_like_space_delimited_inci_run(text: str) -> bool:
    if _HAS_SEPARATOR.search(text):
        return False
    words = _TOKEN_WORD.findall(text)
    if len(words) < 3:
        return False
    letters = "".join(ch for ch in text if ch.isalpha())
    return bool(letters) and letters.upper() == letters


def _segment_space_delimited_run(
    text: str,
    known_terms: Collection[str] | None,
) -> list[str]:
    words = _TOKEN_WORD.findall(text)
    if len(words) < 3:
        return [text]

    normalized_terms = set(_COMMON_SPACE_DELIMITED_INGREDIENTS)
    if known_terms:
        normalized_terms.update(known_terms)
    max_words = min(8, max((len(term.split()) for term in normalized_terms), default=1))
    out: list[str] = []
    i = 0
    while i < len(words):
        best: tuple[int, str] | None = None
        upper = min(len(words), i + max_words)
        for j in range(upper, i, -1):
            candidate = " ".join(words[i:j])
            if normalize_name(candidate) in normalized_terms:
                best = (j, candidate)
                break
        if best:
            i, token = best
            out.append(token)
            continue
        out.append(words[i])
        i += 1
    return out


def _normalized_term_set(known_terms: Collection[str] | None) -> set[str]:
    normalized_terms = set(_COMMON_SPACE_DELIMITED_INGREDIENTS)
    if known_terms:
        normalized_terms.update(known_terms)
    return normalized_terms


def _repair_comma_split_compounds(
    tokens: list[str],
    known_terms: Collection[str] | None,
) -> list[str]:
    normalized_terms = _normalized_term_set(known_terms)
    repaired: list[str] = []
    i = 0
    while i < len(tokens):
        current = tokens[i]
        if i + 1 < len(tokens):
            current_norm = normalize_name(current)
            current_words = normalize_name(current).split()
            next_norm = normalize_name(tokens[i + 1])
            combined = f"{current} {tokens[i + 1]}"
            combined_norm = normalize_name(combined)
            if (
                next_norm in _COMMA_SPLIT_REPAIR_SUFFIX_PHRASES
                and (
                    combined_norm in normalized_terms
                    or " " in next_norm
                    or current_norm not in normalized_terms
                    or (
                        current_words
                        and current_words[-1] in _COMMA_SPLIT_REPAIR_ENDINGS
                    )
                )
            ):
                repaired.append(combined)
                i += 2
                continue
        repaired.append(current)
        i += 1
    return repaired


def _repair_known_sequence_splits(
    tokens: list[str],
    known_terms: Collection[str] | None,
) -> list[str]:
    normalized_terms = _normalized_term_set(known_terms)
    if len(tokens) < 2:
        return tokens

    max_window = min(6, len(tokens))
    repaired: list[str] = []
    i = 0
    while i < len(tokens):
        best: tuple[int, str] | None = None
        for window in range(max_window, 1, -1):
            if i + window > len(tokens):
                continue
            candidate = " ".join(tokens[i : i + window])
            if normalize_name(candidate) in normalized_terms:
                best = (window, candidate)
                break
        if best:
            window, candidate = best
            repaired.append(candidate)
            i += window
            continue
        repaired.append(tokens[i])
        i += 1
    return repaired


def tokenize_label(
    label: str,
    known_terms: Collection[str] | None = None,
) -> list[str]:
    """Split a raw ingredient list from a product label into tokens.

    Handles common separators (comma, semicolon), parenthetical
    concentrations ('Aqua (Water 99%)' -> 'Aqua' + 'Water 99%'),
    label prefixes, common malformed split compounds, and strips
    obvious label noise.
    """
    if not label:
        return []
    label = _extract_ingredient_section(label)
    label = _strip_label_prefix(label)
    label = _strip_may_contain_section(label)
    # Replace bullet-y separators with commas
    label = label.replace("·", ",").replace("•", ",").replace(";", ",").replace("\n", ",")
    parts = []
    for chunk in label.split(","):
        chunk = _clean_token(chunk)
        if not chunk:
            continue
        # Split parenthetical content out as its own token
        depth = 0
        buf = []
        for ch in chunk:
            if ch == "(":
                if buf:
                    parts.append(_clean_token("".join(buf)))
                    buf = []
                depth += 1
            elif ch == ")":
                if buf:
                    parts.append(_clean_token("".join(buf)))
                    buf = []
                depth = max(0, depth - 1)
            else:
                buf.append(ch)
        if buf:
            parts.append(_clean_token("".join(buf)))

    cleaned = [p for p in parts if p and not _is_noise_token(p)]
    cleaned = _repair_comma_split_compounds(cleaned, known_terms)
    cleaned = _repair_known_sequence_splits(cleaned, known_terms)
    out: list[str] = []
    for token in cleaned:
        if _looks_like_space_delimited_inci_run(token):
            out.extend(_segment_space_delimited_run(token, known_terms))
        else:
            out.append(token)
    return [p for p in (s.strip() for s in out) if p and not _is_noise_token(p)]


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out
