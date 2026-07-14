"""normalize_name parity cases with SQL inci_normalize (migration 000600)."""

from __future__ import annotations

from submission_pipeline.normalize import normalize_name, tokenize_label


def test_accents_are_transliterated_not_dropped():
    assert normalize_name("Beurre de Karité") == "beurre de karite"


def test_punctuation_leaves_a_single_space():
    assert normalize_name("Parfum / Fragrance") == "parfum fragrance"


def test_lowercases_and_trims_edges():
    assert normalize_name("  AQUA / WATER  ") == "aqua water"


def test_hyphens_join_without_spaces():
    assert normalize_name("D-Panthenol") == "dpanthenol"


def test_empty_and_symbol_only_input():
    assert normalize_name("") == ""
    assert normalize_name(" /:% ") == ""


def test_drug_facts_headings_percentages_and_bullets_are_not_ingredients():
    label = """**ACTIVE INGREDIENTS (Tinted Shade)** - TITANIUM DIOXIDE 11%
**INACTIVE INGREDIENTS (Tinted Shade)** - WATER• ISODODECANE• C12-15 ALKYL BENZOATE•
DIMETHICONE / PEG-10/15 CROSSPOLYMER• CASSIA ALATA LEAF EXTRACT• DISODIUM STEAROYL GLUTAMATE"""

    assert tokenize_label(label) == [
        "TITANIUM DIOXIDE",
        "WATER",
        "ISODODECANE",
        "C12-15 ALKYL BENZOATE",
        "DIMETHICONE / PEG-10/15 CROSSPOLYMER",
        "CASSIA ALATA LEAF EXTRACT",
        "DISODIUM STEAROYL GLUTAMATE",
    ]


def test_all_caps_fallback_still_segments_labels_without_separators():
    assert tokenize_label("WATER GLYCERIN DIMETHICONE") == [
        "WATER",
        "GLYCERIN",
        "DIMETHICONE",
    ]


def test_commas_and_parenthetical_synonyms_stay_inside_inci_names():
    label = (
        r"WATER\AQUA\EAU, 1,2-HEXANEDIOL, BUTYROSPERMUM PARKII (SHEA) BUTTER, "
        "THEOBROMA CACAO (COCOA) EXTRACT, YELLOW 5 (CI 19140)"
    )

    assert tokenize_label(label) == [
        "WATER/AQUA/EAU",
        "1,2-HEXANEDIOL",
        "BUTYROSPERMUM PARKII (SHEA) BUTTER",
        "THEOBROMA CACAO (COCOA) EXTRACT",
        "YELLOW 5 (CI 19140)",
    ]
