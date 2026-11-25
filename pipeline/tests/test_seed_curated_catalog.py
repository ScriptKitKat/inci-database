import pytest

from scripts import seed_curated_catalog


@pytest.mark.parametrize(
    ("existing_links", "expected_links"),
    [
        (None, [("water-id", 1), ("glycerin-id", 2)]),
        ([{"ingredient_id": "water-id", "position": 4}], [("glycerin-id", 5)]),
        ([{"ingredient_id": "water-id", "position": 4},
          {"ingredient_id": "glycerin-id", "position": 5}], []),
    ],
)
def test_seed_reuses_brand_and_backfills_missing_links(monkeypatch, existing_links, expected_links):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "dummy")
    monkeypatch.setattr(
        seed_curated_catalog,
        "CURATED_PRODUCTS",
        [{
            "brand": "  Example  Brand ",
            "name": "Cleanser",
            "short_description": "Daily cleanser",
            "ingredients": ["Water", "Glycerin", "Water"],
        }],
    )

    added_links = []

    def request(key, method, path, body=None, extra_headers=None):
        if (method, path) == ("POST", "rpc/match_ingredients_batch"):
            assert body == {"inputs": ["Glycerin", "Water"]}
            return [
                {"input_token": "Water", "ingredient_id": "water-id", "confidence": 1.0},
                {"input_token": "Glycerin", "ingredient_id": "glycerin-id", "confidence": 1.0},
            ]
        if (method, path) == ("GET", "brands?select=id,name,slug,normalized&limit=500"):
            return [{"id": "existing-brand", "normalized": "EXAMPLE  BRAND"}]
        if (method, path) == ("GET", "products?slug=eq.example-brand-cleanser&select=id"):
            return [] if existing_links is None else [{"id": "product-id"}]
        if (method, path) == (
            "GET", "product_ingredients?product_id=eq.product-id&select=ingredient_id,position"
        ):
            assert existing_links is not None
            return existing_links
        if (method, path) == ("POST", "products"):
            assert existing_links is None
            assert body["brand_id"] == "existing-brand"
            return [{"id": "product-id"}]
        if (method, path) == ("POST", "product_ingredients"):
            added_links.extend(body)
            return None
        raise AssertionError(f"Unexpected request: {method} {path}")

    monkeypatch.setattr(seed_curated_catalog, "req_json", request)

    assert seed_curated_catalog.main() == 0
    assert added_links == [
        {"product_id": "product-id", "ingredient_id": ingredient_id, "position": position}
        for ingredient_id, position in expected_links
    ]
