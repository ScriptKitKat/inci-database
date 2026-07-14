import httpx

from inci_pipeline.sources.ingredient_verification import (
    ExactIngredientPageLookup,
    OBFIngredientLookup,
    PubChemNameLookup,
    SourceLookupConfig,
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


def test_pubchem_lookup_retries_after_429(monkeypatch):
    calls = {"count": 0, "sleeps": []}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, headers={"retry-after": "0"})
        return httpx.Response(
            200,
            json={
                "InformationList": {
                    "Information": [{"CID": 936, "Synonym": ["Niacinamide"]}]
                }
            },
        )

    monkeypatch.setattr(
        "inci_pipeline.sources.ingredient_verification.time.sleep",
        lambda seconds: calls["sleeps"].append(seconds),
    )
    lookup = PubChemNameLookup(
        config=SourceLookupConfig(max_retries=1, backoff_seconds=0),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    evidence = lookup.lookup("niacinamide")[0]

    assert calls["count"] == 2
    assert evidence.found
    assert evidence.raw_payload["cid"] == 936


def test_pubchem_lookup_retries_after_500(monkeypatch):
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "InformationList": {
                    "Information": [{"CID": 338, "Synonym": ["Salicylic Acid"]}]
                }
            },
        )

    monkeypatch.setattr(
        "inci_pipeline.sources.ingredient_verification.time.sleep",
        lambda seconds: None,
    )
    lookup = PubChemNameLookup(
        config=SourceLookupConfig(max_retries=1, backoff_seconds=0),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    evidence = lookup.lookup("salicylic acid")[0]

    assert calls["count"] == 2
    assert evidence.found
    assert evidence.raw_payload["cid"] == 338


def test_pubchem_lookup_does_not_retry_404():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(404)

    lookup = PubChemNameLookup(
        config=SourceLookupConfig(max_retries=3, backoff_seconds=0),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    evidence = lookup.lookup("not found")[0]

    assert calls["count"] == 1
    assert not evidence.found


def test_lookup_does_not_sleep_on_large_retry_after(monkeypatch):
    calls = {"count": 0, "sleeps": []}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(429, headers={"retry-after": "60"})

    monkeypatch.setattr(
        "inci_pipeline.sources.ingredient_verification.time.sleep",
        lambda seconds: calls["sleeps"].append(seconds),
    )
    lookup = PubChemNameLookup(
        config=SourceLookupConfig(
            max_retries=3,
            max_retry_after_seconds=10,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    evidence = lookup.lookup("niacinamide")[0]

    assert calls["count"] == 1
    assert calls["sleeps"] == []
    assert not evidence.found
    assert evidence.raw_payload["status_code"] == 429
