"""Authoritative spelling and compact enrichment evidence."""

from __future__ import annotations

import httpx
from urllib.parse import parse_qs

from submission_pipeline import evidence


def _pubchem_client(synonyms: list[str]) -> httpx.Client:
    payload = {"InformationList": {"Information": [{"CID": 123, "Synonym": synonyms}]}}
    return httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    )


def test_pubchem_returns_exact_synonym_rendering():
    lookup = evidence.PubChemLookup(client=_pubchem_client(["nicotinamide", "Niacinamide"]))
    ev = lookup.lookup("niacinamide")
    assert ev.found
    assert ev.canonical == "Niacinamide"
    assert ev.confidence == evidence.PUBCHEM_CONFIDENCE


def test_pubchem_without_exact_synonym_is_not_found():
    lookup = evidence.PubChemLookup(client=_pubchem_client(["3-Pyridinecarboxamide", "Vitamin PP"]))
    ev = lookup.lookup("niacinamide")
    assert not ev.found
    assert ev.canonical is None


def test_pubchem_is_not_a_spelling_source():
    assert "pubchem" not in evidence.SPELLING_SOURCES
    assert "open_beauty_facts" not in evidence.SPELLING_SOURCES
    assert evidence.SPELLING_SOURCES == {"cosing", "incidecoder"}


def test_confidence_ranks_official_registry_highest():
    assert (
        evidence.COSING_CONFIDENCE > evidence.INCIDECODER_CONFIDENCE > evidence.PUBCHEM_CONFIDENCE
    )


def test_cosing_uses_exact_post_and_captures_enrichment():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        form = parse_qs(request.content.decode())
        assert form["text"] == ['"hyaluronic acid"']
        assert form["pageSize"] == ["5"]
        assert form["apiKey"] == [evidence.COSING_API_KEY]
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "metadata": {
                            "inciName": ["HYALURONIC ACID"],
                            "casNo": ["9004-61-9"],
                            "ecNo": ["232-678-0"],
                            "substanceId": ["34315"],
                            "chemicalName": ["Hyaluronic acid"],
                            "chemicalDescription": ["A glycosaminoglycan"],
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    ev = evidence.CosIngSearchLookup(client).lookup("hyaluronic acid")
    assert ev.found
    assert ev.canonical == "Hyaluronic Acid"
    assert ev.enrichment == {
        "inci_name": "HYALURONIC ACID",
        "cas_number": "9004-61-9",
        "ec_number": "232-678-0",
        "substance_id": "34315",
        "chemical_name": "Hyaluronic acid",
        "description": "A glycosaminoglycan",
    }


def test_cosing_omits_empty_metadata_arrays():
    payload = {
        "results": [
            {
                "metadata": {
                    "inciName": ["WATER"],
                    "casNo": ["7732-18-5"],
                    "ecNo": [],
                    "chemicalDescription": [],
                }
            }
        ]
    }
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    )
    ev = evidence.CosIngSearchLookup(client).lookup("water")
    assert ev.enrichment == {"inci_name": "WATER", "cas_number": "7732-18-5"}


def test_cosing_refreshes_rotated_key_once():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url == evidence.COSING_CONFIG_URL:
            return httpx.Response(200, json={"euSearchApiKey": "rotated"})
        form = parse_qs(request.content.decode())
        if form["apiKey"] != ["rotated"]:
            return httpx.Response(401)
        return httpx.Response(200, json={"results": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert not evidence.CosIngSearchLookup(client).lookup("water").found
    assert [request.method for request in calls] == ["POST", "GET", "POST"]


def test_incidecoder_title_fallback_removes_display_suffix():
    assert (
        evidence._page_canonical("<title>Hyaluronic Acid (Explained + Products)</title>")
        == "Hyaluronic Acid"
    )
    assert evidence._page_canonical("<h1>C12-15 Alkyl Benzoate &amp; Water</h1>") == (
        "C12-15 Alkyl Benzoate & Water"
    )


def test_incidecoder_falls_back_to_first_search_result():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/ingredients/sodium-hyaloronate":
            return httpx.Response(404)
        if request.url.path == "/search":
            assert request.url.params["query"] == "sodium hyaloronate"
            return httpx.Response(200, text='<a href="/ingredients/sodium-hyaluronate">result</a>')
        return httpx.Response(200, text="<h1>Sodium Hyaluronate</h1>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    ev = evidence.INCIDecoderLookup(client).lookup("sodium hyaloronate")
    assert ev.found
    assert ev.canonical == "Sodium Hyaluronate"
