from inci_pipeline.normalize import (
    dedupe_preserve_order,
    ingredient_fingerprint,
    normalize_brand_name,
    normalize_name,
    slug,
    tokenize_label,
)


def test_normalize_lowercases_and_strips_punctuation():
    assert normalize_name("Salicylic Acid") == "salicylic acid"
    assert normalize_name("Salicylic-Acid (USP)") == "salicylicacid usp"
    assert normalize_name("Caprylic/Capric Triglyceride") == "capryliccapric triglyceride"


def test_normalize_strips_diacritics():
    assert normalize_name("Café") == "cafe"
    assert normalize_name("Tocophérol") == "tocopherol"


def test_normalize_collapses_whitespace():
    assert normalize_name("  Aloe   Barbadensis  ") == "aloe barbadensis"


def test_normalize_handles_empty():
    assert normalize_name("") == ""


def test_slug():
    assert slug("Salicylic Acid") == "salicylic-acid"
    assert slug("Beta-Hydroxy Acid (BHA)") == "beta-hydroxy-acid-bha"


def test_tokenize_label_basic():
    raw = "Aqua, Glycerin, Salicylic Acid, Niacinamide"
    assert tokenize_label(raw) == ["Aqua", "Glycerin", "Salicylic Acid", "Niacinamide"]


def test_tokenize_label_strips_parentheticals_as_separate_tokens():
    raw = "Aqua (Water), Glycerin"
    tokens = tokenize_label(raw)
    assert "Aqua" in tokens
    assert "Water" in tokens
    assert "Glycerin" in tokens


def test_tokenize_label_drops_noise():
    raw = "Ingredients: Aqua, Glycerin, may contain CI 77891"
    tokens = tokenize_label(raw)
    assert tokens == ["Aqua", "Glycerin"]


def test_tokenize_label_drops_punctuation_only_values():
    assert tokenize_label(".") == []


def test_tokenize_label_strips_malformed_ingredients_prefix():
    assert tokenize_label("NGREDIENTS: AQUA") == ["AQUA"]
    assert tokenize_label("INGREDIENTS AQUA") == ["AQUA"]


def test_tokenize_label_segments_comma_less_uppercase_inci_runs():
    raw = "AQUA/WATER/EAU GLYCERIN BUTYLENE GLYCOL"
    assert tokenize_label(raw) == ["AQUA/WATER/EAU", "GLYCERIN", "BUTYLENE GLYCOL"]


def test_tokenize_label_repairs_comma_split_botanical_oils():
    assert tokenize_label("Castor seed, oil") == ["Castor seed oil"]


def test_tokenize_label_repairs_comma_split_shea_butter():
    assert tokenize_label("Shea, butter") == ["Shea butter"]


def test_tokenize_label_repairs_known_adjacent_compounds():
    known_terms = {"cocos nucifera oil"}
    assert tokenize_label("Cocos nucifera, oil", known_terms=known_terms) == [
        "Cocos nucifera oil"
    ]


def test_tokenize_label_repairs_two_word_suffix_compounds():
    assert tokenize_label("Soybean, seed extract") == ["Soybean seed extract"]


def test_tokenize_label_does_not_merge_known_standalone_with_suffix():
    known_terms = {"glycerin", "water"}
    assert tokenize_label("Glycerin, water", known_terms=known_terms) == [
        "Glycerin",
        "water",
    ]


def test_tokenize_label_drops_single_letter_noise():
    assert tokenize_label("Aqua, F, I, L, Glycerin") == ["Aqua", "Glycerin"]


def test_tokenize_label_drops_directions_without_ingredients():
    raw = "Directions: Apply a sufficient amount of lotion onto cleansed face, neck and hands. Use daily"
    assert tokenize_label(raw) == []


def test_tokenize_label_drops_lot_codes():
    assert tokenize_label("LOT 31689A") == []


def test_tokenize_label_extracts_ingredients_after_directions():
    raw = "Directions: Apply to underarms. Ingredients: Caprylic/Capric Triglyceride, Glycerin"
    assert tokenize_label(raw) == ["Caprylic/Capric Triglyceride", "Glycerin"]


def test_tokenize_label_strips_instruction_tail():
    raw = "Ingredients: Aqua, Glycerin. Directions: Apply daily"
    assert tokenize_label(raw) == ["Aqua", "Glycerin"]


def test_tokenize_label_keeps_non_uppercase_aqua_water_together():
    assert tokenize_label("Aqua water") == ["Aqua water"]


def test_tokenize_label_uses_known_terms_for_longest_match():
    known_terms = {"aqua", "glycerin", "butylene glycol"}
    raw = "AQUA GLYCERIN BUTYLENE GLYCOL"
    assert tokenize_label(raw, known_terms=known_terms) == ["AQUA", "GLYCERIN", "BUTYLENE GLYCOL"]


def test_tokenize_label_repairs_known_sequence_splits():
    known_terms = {
        "peg40 hydrogenated castor oil",
        "acrylatesc1030 alkyl acrylate crosspolymer",
    }
    assert tokenize_label(
        "PEG-40, HYDROGENATED, CASTOR OIL",
        known_terms=known_terms,
    ) == ["PEG-40 HYDROGENATED CASTOR OIL"]
    assert tokenize_label(
        "ACRYLATES/C10-30, ALKYL, ACRYLATE, CROSSPOLYMER",
        known_terms=known_terms,
    ) == ["ACRYLATES/C10-30 ALKYL ACRYLATE CROSSPOLYMER"]


def test_ingredient_fingerprint_preserves_order():
    first = ingredient_fingerprint(["Aqua", "Glycerin"])
    second = ingredient_fingerprint(["Glycerin", "Aqua"])
    assert first != second
    assert first == ingredient_fingerprint([" Aqua ", "GLYCERIN"])


def test_normalize_brand_name():
    assert normalize_brand_name("  CeraVe   ") == "CERAVE"
    assert normalize_brand_name(None) == ""


def test_dedupe_preserve_order():
    assert dedupe_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
