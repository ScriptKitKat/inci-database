from io import BytesIO

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
def test_seed_reuses_brand_and_backfills_missing_links(
    monkeypatch, capsys, existing_links, expected_links
):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "dummy")
    monkeypatch.setattr(
        seed_curated_catalog,
        "CURATED_PRODUCTS",
        [{
            "brand": "  Example  Brand ",
            "name": "Cleanser",
            "short_description": "Daily cleanser",
            "ingredients": ["Water", "Glycerin", "Water", "sh-Oligopeptide-1"],
        }],
    )

    added_links = []

    def request(key, method, path, body=None, extra_headers=None):
        if (method, path) == ("POST", "rpc/match_ingredients_batch"):
            assert body == {"inputs": ["Glycerin", "Water", "sh-Oligopeptide-1"]}
            return [
                {"input_token": "Water", "ingredient_id": "water-id",
                 "confidence": 1.0, "match_type": "canonical_exact"},
                {"input_token": "Glycerin", "ingredient_id": "glycerin-id",
                 "confidence": 0.98, "match_type": "alias_exact"},
                {"input_token": "sh-Oligopeptide-1", "ingredient_id": "oligopeptide-2-id",
                 "confidence": 0.92, "match_type": "alias_fuzzy"},
            ]
        if (method, path) == ("GET", "brands?select=id,name,slug,normalized&limit=500"):
            return [{"id": "existing-brand", "normalized": "EXAMPLE  BRAND"}]
        if (method, path) == ("POST", "rpc/find_product_by_identity"):
            assert body == {"p_brand_name": "  Example  Brand ", "p_product_name": "Cleanser"}
            return [] if existing_links is None else [{"product_id": "product-id"}]
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
    assert "Unmatched or fuzzy tokens (skipped): ['sh-Oligopeptide-1']" in capsys.readouterr().out
    assert added_links == [
        {"product_id": "product-id", "ingredient_id": ingredient_id, "position": position}
        for ingredient_id, position in expected_links
    ]


@pytest.mark.parametrize("key", ["header.payload.signature", "sb_secret_example"])
def test_seed_request_authenticates_service_role(monkeypatch, key):
    def urlopen(request, timeout):
        assert request.get_header("Apikey") == key
        assert request.get_header("Authorization") == (
            f"Bearer {key}" if key == "header.payload.signature" else None
        )
        return BytesIO(b"[]")

    monkeypatch.setattr(seed_curated_catalog.urllib.request, "urlopen", urlopen)

    assert seed_curated_catalog.req_json(key, "POST", "rpc/find_product_by_identity") == []
