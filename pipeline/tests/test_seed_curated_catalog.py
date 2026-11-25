from scripts import seed_curated_catalog


def test_seed_reuses_existing_brand_by_database_normalized_name(monkeypatch):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "dummy")
    monkeypatch.setattr(
        seed_curated_catalog,
        "CURATED_PRODUCTS",
        [{
            "brand": "  Example  Brand ",
            "name": "Cleanser",
            "short_description": "Daily cleanser",
            "ingredients": ["Water"],
        }],
    )

    def request(key, method, path, body=None, extra_headers=None):
        if (method, path) == ("POST", "rpc/match_ingredients_batch"):
            assert body == {"inputs": ["Water"]}
            return [{"input_token": "Water", "ingredient_id": "water-id", "confidence": 1.0}]
        if (method, path) == ("GET", "brands?select=id,name,slug,normalized&limit=500"):
            return [{"id": "existing-brand", "normalized": "EXAMPLE  BRAND"}]
        if (method, path) == ("GET", "products?slug=eq.example-brand-cleanser&select=id"):
            return []
        if (method, path) == ("POST", "products"):
            assert body["brand_id"] == "existing-brand"
            return [{"id": "new-product"}]
        if (method, path) == ("POST", "product_ingredients"):
            assert body == [
                {"product_id": "new-product", "ingredient_id": "water-id", "position": 1},
            ]
            return None
        raise AssertionError(f"Unexpected request: {method} {path}")

    monkeypatch.setattr(seed_curated_catalog, "req_json", request)

    assert seed_curated_catalog.main() == 0
