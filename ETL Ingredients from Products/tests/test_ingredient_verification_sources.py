import httpx

from inci_pipeline.sources.ingredient_verification import (
    ExactIngredientPageLookup,
    OBFIngredientLookup,
)


def test_exact_page_lookup_confirms_normalized_name():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/niacinamide")
        return httpx.Response(
            200,
            text="<html><title>Niacinamide | Ingredient</title><h1>Niacinamide</h1></html>",
        )

    lookup = ExactIngredientPageLookup(
        "example",
        "https://example.test/ingredients/{slug}",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    evidence = lookup.lookup("niacinamide")[0]
    assert evidence.found
    assert evidence.normalized_canonical == "niacinamide"


def test_exact_page_lookup_not_found_on_404():
    lookup = ExactIngredientPageLookup(
        "example",
        "https://example.test/ingredients/{slug}",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(404))
        ),
    )
    evidence = lookup.lookup("madeup")[0]
    assert not evidence.found
    assert evidence.raw_payload["status_code"] == 404


def test_obf_lookup_matches_alias(tmp_path):
    path = tmp_path / "ingredients.txt"
    path.write_text("en: Niacinamide, Vitamin B3\n", encoding="utf-8")
    evidence = OBFIngredientLookup(path).lookup("vitamin b3")[0]
    assert evidence.found
    assert evidence.lookup_type == "alias"
    assert evidence.normalized_canonical == "niacinamide"
