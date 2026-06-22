"""PubMed E-utilities client.

NCBI rate limit is 3 req/sec without an API key, 10 with. Set
NCBI_API_KEY in the env to lift the cap.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from lxml import etree
from tenacity import retry, stop_after_attempt, wait_exponential

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


@dataclass(frozen=True)
class PubMedAbstract:
    pmid: str
    title: str
    abstract: str
    journal: str | None
    year: int | None

    @property
    def url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"


class PubMedClient:
    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self._client = client or httpx.Client(timeout=20.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PubMedClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _params(self, extra: dict[str, str]) -> dict[str, str]:
        base = {"db": "pubmed", "retmode": "xml"}
        base.update(extra)
        if self.api_key:
            base["api_key"] = self.api_key
        return base

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=5))
    def search(self, inci_name: str, cas: str | None = None, max_results: int = 5) -> list[str]:
        term = f'"{inci_name}"[tiab]'
        if cas:
            term = f"({term} OR {cas}[rn])"
        params = self._params(
            {"term": term, "retmax": str(max_results), "sort": "relevance"}
        )
        resp = self._client.get(ESEARCH, params=params)
        resp.raise_for_status()
        root = etree.fromstring(resp.content)
        return [el.text for el in root.findall(".//IdList/Id") if el.text]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=5))
    def fetch(self, pmids: list[str]) -> list[PubMedAbstract]:
        if not pmids:
            return []
        params = self._params({"id": ",".join(pmids), "rettype": "abstract"})
        resp = self._client.get(EFETCH, params=params)
        resp.raise_for_status()
        root = etree.fromstring(resp.content)
        out: list[PubMedAbstract] = []
        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            title_el = article.find(".//ArticleTitle")
            journal_el = article.find(".//Journal/Title")
            year_el = article.find(".//PubDate/Year")
            abstract_texts = [
                (t.text or "")
                for t in article.findall(".//Abstract/AbstractText")
            ]
            if pmid_el is None or title_el is None:
                continue
            out.append(
                PubMedAbstract(
                    pmid=pmid_el.text or "",
                    title=title_el.text or "",
                    abstract=" ".join(t.strip() for t in abstract_texts if t).strip(),
                    journal=journal_el.text if journal_el is not None else None,
                    year=int(year_el.text) if year_el is not None and year_el.text else None,
                )
            )
        return out
