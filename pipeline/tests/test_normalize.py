from inci_pipeline.normalize import dedupe_preserve_order, normalize_name, slug, tokenize_label


def test_normalize_lowercases_and_strips_punctuation():
    assert normalize_name("Salicylic Acid") == "salicylic acid"
    assert normalize_name("Salicylic-Acid (USP)") == "salicylic acid usp"


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
    assert "Aqua" in tokens
    assert "Glycerin" in tokens
    # "may contain" and "ingredients" are noise, dropped
    assert "may contain" not in tokens
    assert "Ingredients" not in tokens


def test_dedupe_preserve_order():
    assert dedupe_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
