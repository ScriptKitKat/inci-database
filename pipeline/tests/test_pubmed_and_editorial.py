"""Tests for PubMed dermatology scoping and PMID propagation into editorial prompts."""

from __future__ import annotations

import httpx
import respx

from inci_pipeline.llm.claude import build_editorial_prompt
from inci_pipeline.sources.pubmed import ESEARCH, PubMedClient


@respx.mock
def test_pubmed_search_prefers_skin_scoped_results() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.params["term"])
        return httpx.Response(
            200,
            content=b"<eSearchResult><IdList><Id>12345678</Id></IdList></eSearchResult>",
        )

    respx.get(ESEARCH).mock(side_effect=handler)

    with PubMedClient() as pm:
        pmids = pm.search("Salicylic Acid", cas="69-72-7", max_results=5)

    assert pmids == ["12345678"]
    assert len(calls) == 1
    assert "skin[tiab]" in calls[0]
    assert "69-72-7[rn]" in calls[0]


@respx.mock
def test_pubmed_search_falls_back_when_scoped_empty() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        term = request.url.params["term"]
        calls.append(term)
        if "skin[tiab]" in term:
            return httpx.Response(200, content=b"<eSearchResult><IdList/></eSearchResult>")
        return httpx.Response(
            200,
            content=b"<eSearchResult><IdList><Id>99999999</Id></IdList></eSearchResult>",
        )

    respx.get(ESEARCH).mock(side_effect=handler)

    with PubMedClient() as pm:
        pmids = pm.search("Rare Botanical Extract", max_results=3)

    assert pmids == ["99999999"]
    assert len(calls) == 2
    assert "skin[tiab]" in calls[0]
    assert "skin[tiab]" not in calls[1]


def test_build_editorial_prompt_uses_external_id_for_pmid() -> None:
    prompt = build_editorial_prompt(
        inci_name="Niacinamide",
        function_tags=["skin_conditioning"],
        is_restricted_eu=False,
        is_restricted_us=False,
        abstracts=[
            {
                "external_id": "16029679",
                "title": "Niacinamide clinical trial",
                "raw_payload": {"year": 2005, "abstract": "Improved tone and barrier."},
            }
        ],
    )
    assert "PMID: 16029679" in prompt
    assert "PMID: unknown" not in prompt
