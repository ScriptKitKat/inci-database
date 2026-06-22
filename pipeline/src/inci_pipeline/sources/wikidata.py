"""Wikidata SPARQL client.

Used to enrich ingredients with EC numbers (P232), InChI (P234), and
chemical formula (P274) by looking up Wikidata items via CAS number
(P231). We batch CAS numbers into a single VALUES clause per query to
keep round-trips low.

Wikidata enforces a User-Agent policy — see
https://meta.wikimedia.org/wiki/User-Agent_policy. Pass a contact
identifier when instantiating in production.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

SPARQL_URL = "https://query.wikidata.org/sparql"
DEFAULT_UA = "inci-database/0.1 (https://github.com/anonymous/inci-database)"


@dataclass(frozen=True)
class WikidataRecord:
    cas: str
    item_uri: str
    ec: str | None
    inchi: str | None
    formula: str | None


class WikidataClient:
    def __init__(self, user_agent: str = DEFAULT_UA, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            timeout=60.0,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/sparql-results+json",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "WikidataClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def lookup_by_cas(self, cas_numbers: Iterable[str]) -> list[WikidataRecord]:
        cas_list = [c for c in cas_numbers if c]
        if not cas_list:
            return []
        values = " ".join(f'"{c}"' for c in cas_list)
        query = f"""
        SELECT ?item ?cas ?ec ?inchi ?formula WHERE {{
          VALUES ?cas {{ {values} }}
          ?item wdt:P231 ?cas .
          OPTIONAL {{ ?item wdt:P232 ?ec . }}
          OPTIONAL {{ ?item wdt:P234 ?inchi . }}
          OPTIONAL {{ ?item wdt:P274 ?formula . }}
        }}
        """
        resp = self._client.get(SPARQL_URL, params={"query": query, "format": "json"})
        resp.raise_for_status()
        bindings = resp.json().get("results", {}).get("bindings", [])
        return [
            WikidataRecord(
                cas=b["cas"]["value"],
                item_uri=b["item"]["value"],
                ec=b.get("ec", {}).get("value"),
                inchi=b.get("inchi", {}).get("value"),
                formula=b.get("formula", {}).get("value"),
            )
            for b in bindings
        ]


def chunked(items: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
