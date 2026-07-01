"""Evidence lookups for normalized ingredient-name curation."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import certifi
import httpx

from ..curation.models import IngredientEvidence
from ..normalize import normalize_name, slug
from . import obf_taxonomy

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"


@dataclass(frozen=True)
class SourceLookupConfig:
    timeout: float = 10.0
    user_agent: str = "inci-database/0.1 ingredient-curation"
    max_retries: int = 3
    backoff_seconds: float = 1.0
    max_backoff_seconds: float = 30.0
    max_retry_after_seconds: float = 10.0


class OBFIngredientLookup:
    def __init__(self, taxonomy_path: Path) -> None:
        self._taxonomy_path = taxonomy_path
        self._canonicals: dict[str, str] = {}
        self._aliases: dict[str, str] = {}
        if taxonomy_path.exists():
            for entry in obf_taxonomy.parse(taxonomy_path):
                canonical_norm = normalize_name(entry.en_canonical)
                if canonical_norm:
                    self._canonicals[canonical_norm] = entry.en_canonical
                for alias in entry.en_synonyms:
                    alias_norm = normalize_name(alias)
                    if alias_norm:
                        self._aliases.setdefault(alias_norm, entry.en_canonical)

    def lookup(self, normalized_name: str) -> list[IngredientEvidence]:
        if normalized_name in self._canonicals:
            return [
                IngredientEvidence(
                    source="open_beauty_facts",
                    lookup_type="exact",
                    found=True,
                    canonical_name=self._canonicals[normalized_name],
                    normalized_canonical=normalized_name,
                    confidence=0.95,
                    raw_payload={"file": str(self._taxonomy_path)},
                )
            ]
        if normalized_name in self._aliases:
            canonical = self._aliases[normalized_name]
            return [
                IngredientEvidence(
                    source="open_beauty_facts",
                    lookup_type="alias",
                    found=True,
                    canonical_name=canonical,
                    normalized_canonical=normalize_name(canonical),
                    confidence=0.92,
                    raw_payload={"file": str(self._taxonomy_path)},
                )
            ]
        return [_not_found("open_beauty_facts", "exact")]


class PubChemNameLookup:
    def __init__(
        self,
        config: SourceLookupConfig | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._config = config or SourceLookupConfig()
        self._client = client or httpx.Client(
            timeout=self._config.timeout,
            headers={"User-Agent": self._config.user_agent},
            verify=certifi.where(),
        )

    def close(self) -> None:
        self._client.close()

    def lookup(self, normalized_name: str) -> list[IngredientEvidence]:
        name = quote(normalized_name)
        url = f"{PUBCHEM_BASE}/compound/name/{name}/synonyms/JSON"
        resp = _get_with_retry(self._client, url, config=self._config)
        if resp.status_code in (400, 404):
            return [_not_found("pubchem", "exact", url)]
        if resp.status_code != 200:
            return [_not_found("pubchem", "exact", url, {"status_code": resp.status_code})]
        payload = resp.json()
        info = payload.get("InformationList", {}).get("Information", [{}])[0]
        cid = info.get("CID")
        synonyms = info.get("Synonym", []) or []
        canonical = _best_synonym(normalized_name, synonyms) or normalized_name
        lookup_type = "exact" if normalize_name(canonical) == normalized_name else "alias"
        return [
            IngredientEvidence(
                source="pubchem",
                lookup_type=lookup_type,
                found=True,
                canonical_name=canonical,
                normalized_canonical=normalize_name(canonical),
                url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else url,
                confidence=0.90 if lookup_type == "exact" else 0.84,
                raw_payload={"cid": cid, "synonyms": synonyms[:20]},
            )
        ]


class WikidataNameLookup:
    def __init__(
        self,
        config: SourceLookupConfig | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._config = config or SourceLookupConfig()
        self._client = client or httpx.Client(
            timeout=self._config.timeout,
            headers={
                "User-Agent": self._config.user_agent,
                "Accept": "application/sparql-results+json",
            },
            verify=certifi.where(),
        )

    def close(self) -> None:
        self._client.close()

    def lookup(self, normalized_name: str) -> list[IngredientEvidence]:
        query = """
        SELECT ?item ?itemLabel ?alias WHERE {
          ?item rdfs:label|skos:altLabel ?label .
          FILTER(LANG(?label) = "en")
          FILTER(LCASE(STR(?label)) = "%s")
          OPTIONAL { ?item skos:altLabel ?alias FILTER(LANG(?alias) = "en") }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT 5
        """ % normalized_name.replace('"', '\\"')
        resp = _get_with_retry(
            self._client,
            WIKIDATA_SPARQL,
            config=self._config,
            params={"query": query, "format": "json"},
        )
        if resp.status_code != 200:
            return [_not_found("wikidata", "exact", raw_payload={"status_code": resp.status_code})]
        bindings = resp.json().get("results", {}).get("bindings", [])
        if not bindings:
            return [_not_found("wikidata", "exact")]
        first = bindings[0]
        canonical = first.get("itemLabel", {}).get("value") or normalized_name
        item = first.get("item", {}).get("value")
        return [
            IngredientEvidence(
                source="wikidata",
                lookup_type="exact" if normalize_name(canonical) == normalized_name else "alias",
                found=True,
                canonical_name=canonical,
                normalized_canonical=normalize_name(canonical),
                url=item,
                confidence=0.82,
                raw_payload={"bindings": bindings[:5]},
            )
        ]


class ExactIngredientPageLookup:
    def __init__(
        self,
        source: str,
        url_template: str,
        *,
        config: SourceLookupConfig | None = None,
        client: httpx.Client | None = None,
        canonical_pattern: str | None = None,
    ) -> None:
        self._source = source
        self._url_template = url_template
        self._config = config or SourceLookupConfig()
        self._client = client or httpx.Client(
            timeout=self._config.timeout,
            headers={"User-Agent": self._config.user_agent},
            follow_redirects=True,
            verify=certifi.where(),
        )
        self._canonical_re = re.compile(canonical_pattern, re.I | re.S) if canonical_pattern else None

    def close(self) -> None:
        self._client.close()

    def lookup(self, normalized_name: str) -> list[IngredientEvidence]:
        page_slug = slug(normalized_name)
        url = self._url_template.format(slug=page_slug)
        resp = _get_with_retry(self._client, url, config=self._config)
        if resp.status_code != 200:
            return [_not_found(self._source, "page", url, {"status_code": resp.status_code})]
        text = resp.text
        canonical = _extract_title(text) or normalized_name
        if self._canonical_re:
            match = self._canonical_re.search(text)
            if match:
                canonical = _strip_html(match.group(1))
        found = _page_confirms_name(text, normalized_name)
        return [
            IngredientEvidence(
                source=self._source,
                lookup_type="page",
                found=found,
                canonical_name=canonical if found else None,
                normalized_canonical=normalize_name(canonical) if found else None,
                url=url,
                confidence=0.88 if found else 0.0,
                raw_payload={
                    "status_code": resp.status_code,
                    "exact_slug": page_slug,
                    "title": _extract_title(text),
                },
            )
        ]


def incidecoder_lookup(
    client: httpx.Client | None = None,
    config: SourceLookupConfig | None = None,
) -> ExactIngredientPageLookup:
    return ExactIngredientPageLookup(
        "incidecoder",
        "https://incidecoder.com/ingredients/{slug}",
        config=config,
        client=client,
        canonical_pattern=r"<h1[^>]*>(.*?)</h1>",
    )


def specialchem_lookup(
    client: httpx.Client | None = None,
    config: SourceLookupConfig | None = None,
) -> ExactIngredientPageLookup:
    return ExactIngredientPageLookup(
        "specialchem",
        "https://www.specialchem.com/cosmetics/inci-ingredients/{slug}",
        config=config,
        client=client,
        canonical_pattern=r"<h1[^>]*>(.*?)</h1>",
    )


def _best_synonym(normalized_name: str, synonyms: list[str]) -> str | None:
    for syn in synonyms:
        if normalize_name(syn) == normalized_name:
            return syn
    return synonyms[0] if synonyms else None


def _get_with_retry(
    client: httpx.Client,
    url: str,
    *,
    config: SourceLookupConfig,
    params: dict | None = None,
) -> httpx.Response:
    last_exc: httpx.HTTPError | None = None
    for attempt in range(config.max_retries + 1):
        try:
            resp = client.get(url, params=params)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_exc = exc
            if attempt >= config.max_retries:
                raise
            _sleep_before_retry(attempt, config=config)
            continue

        if not _should_retry_status(resp.status_code) or attempt >= config.max_retries:
            return resp
        retry_after = _retry_after_seconds(resp.headers.get("retry-after"))
        if retry_after is not None and retry_after > config.max_retry_after_seconds:
            return resp
        _sleep_before_retry(attempt, config=config, retry_after_seconds=retry_after)

    if last_exc:
        raise last_exc
    raise RuntimeError("unreachable retry state")


def _should_retry_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code < 600


def _sleep_before_retry(
    attempt: int,
    *,
    config: SourceLookupConfig,
    retry_after_seconds: float | None = None,
) -> None:
    delay = retry_after_seconds
    if delay is None:
        delay = min(config.backoff_seconds * (2**attempt), config.max_backoff_seconds)
    if delay > 0:
        time.sleep(delay)


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, retry_at.timestamp() - time.time())


def _not_found(
    source: str,
    lookup_type: str,
    url: str | None = None,
    raw_payload: dict | None = None,
) -> IngredientEvidence:
    return IngredientEvidence(
        source=source,
        lookup_type=lookup_type,
        found=False,
        url=url,
        raw_payload=raw_payload or {},
    )


def _extract_title(text: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if not match:
        return None
    title = _strip_html(match.group(1))
    return title.split("|", 1)[0].strip() or None


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _page_confirms_name(text: str, normalized_name: str) -> bool:
    normalized_text = normalize_name(_strip_html(text))
    return normalized_name in normalized_text
