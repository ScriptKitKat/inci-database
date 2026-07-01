from __future__ import annotations

from dataclasses import dataclass

MEANINGFUL_MODIFIERS = {
    "acetyl",
    "crosspolymer",
    "extract",
    "ferment",
    "flower",
    "glucoside",
    "hydrolyzed",
    "leaf",
    "lysate",
    "magnesium",
    "oil",
    "palmitate",
    "phosphate",
    "potassium",
    "root",
    "seed",
    "sodium",
}


@dataclass(frozen=True)
class NameScore:
    target_ingredient_id: str
    target_normalized_name: str
    similarity: float
    edit_distance: int
    token_overlap: float
    score_margin: float | None = None


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (0 if ca == cb else 1),
                )
            )
        previous = current
    return previous[-1]


def trigram_similarity(a: str, b: str) -> float:
    """Approximate PostgreSQL pg_trgm similarity for local tests/fallbacks."""
    ta = _trigrams(a)
    tb = _trigrams(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return (2.0 * len(ta & tb)) / (len(ta) + len(tb))


def token_overlap(a: str, b: str) -> float:
    left = set(a.split())
    right = set(b.split())
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def has_meaningful_modifier_difference(a: str, b: str) -> bool:
    left = set(a.split()) & MEANINGFUL_MODIFIERS
    right = set(b.split()) & MEANINGFUL_MODIFIERS
    return left != right


def is_spelling_merge_candidate(source_normalized_name: str, score: NameScore) -> bool:
    if has_meaningful_modifier_difference(source_normalized_name, score.target_normalized_name):
        return False
    if score.score_margin is not None and score.score_margin < 0.05:
        return False
    name_len = len(score.target_normalized_name)
    if name_len <= 8:
        return score.edit_distance <= 1 and score.similarity >= 0.80
    if name_len <= 20:
        return score.edit_distance <= 2 or score.similarity >= 0.92
    return score.similarity >= 0.88 and score.token_overlap >= 0.60


def _trigrams(text: str) -> set[str]:
    words = [f"  {word} " for word in text.split() if word]
    grams: set[str] = set()
    for word in words:
        grams.update(word[i : i + 3] for i in range(len(word) - 2))
    return grams
