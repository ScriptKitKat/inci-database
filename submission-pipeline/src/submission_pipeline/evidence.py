"""Authoritative-source evidence lookups for submitted ingredient tokens.

Sources: PubChem exact-name lookup, the CosIng registry search API, and
INCIDecoder ingredient pages. Every lookup returns compact
`Evidence` — no raw payloads are kept. Only `SPELLING_SOURCES` may donate
a new ingredient's `canonical_name`; PubChem corroborates existence only.
CosIng's words and punctuation are preserved, with the plan's casing-only
Title Case transform; its original rendering remains in enrichment metadata.
"""

from __future__ import annotations

import logging
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any, Protocol
from urllib.parse import quote, urljoin

import certifi
import httpx

from .models import Evidence
from .normalize import normalize_name, slug

logger = logging.getLogger(__name__)

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
COSING_SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
COSING_CONFIG_URL = "https://ec.europa.eu/growth/tools-databases/cosing/assets/env-json-config.json"
COSING_API_KEY = "285a77fd-1257-4271-8507-f0c6b2961203"
INCIDECODER_URL_TEMPLATE = "https://incidecoder.com/ingredients/{slug}"
INCIDECODER_SEARCH_URL = "https://incidecoder.com/search"

# Only INCI-native sources may donate a canonical spelling. PubChem is a
# chemistry database — its renderings (all-caps synonyms, IUPAC names) are
# not INCI names — so its evidence corroborates that a substance exists but
# must never supply `canonical_name`.
SPELLING_SOURCES = frozenset({"cosing", "incidecoder"})

# Trust order: CosIng is the European Commission ingredient database,
# INCIDecoder is INCI-curated, and PubChem is corroboration-only.
COSING_CONFIDENCE = 0.97
INCIDECODER_CONFIDENCE = 0.92
PUBCHEM_CONFIDENCE = 0.85

TIMEOUT_SECONDS = 10.0
USER_AGENT = "inci-database/0.1 submission-pipeline"
MAX_RETRIES = 3
BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 30.0
MAX_RETRY_AFTER_SECONDS = 10.0


class Lookup(Protocol):
    source: str

    def lookup(self, normalized: str) -> Evidence: ...


class PubChemLookup:
    """Exact-name compound lookup; corroboration-only, never donates a spelling."""

    source = "pubchem"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or _http_client()

    def close(self) -> None:
        self._client.close()

    def lookup(self, normalized: str) -> Evidence:
        url = f"{PUBCHEM_BASE}/compound/name/{quote(normalized)}/synonyms/JSON"
        resp = _get_with_retry(self._client, url)
        if resp.status_code != 200:
            return Evidence(source=self.source, found=False, url=url)
        payload = resp.json()
        info = payload.get("InformationList", {}).get("Information", [{}])[0]
        cid = info.get("CID")
        synonyms = info.get("Synonym", []) or []
        canonical = _exact_synonym(normalized, synonyms)
        if not canonical:
            return Evidence(source=self.source, found=False, url=url)
        return Evidence(
            source=self.source,
            found=True,
            canonical=canonical,
            url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else url,
            confidence=PUBCHEM_CONFIDENCE,
        )


class CosIngSearchLookup:
    """Exact INCI-name hit against the European Commission search API."""

    source = "cosing"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or _http_client()
        self._api_key = COSING_API_KEY

    def close(self) -> None:
        self._client.close()

    def lookup(self, normalized: str) -> Evidence:
        try:
            resp = self._search(normalized)
            if resp.status_code == 401 and self._refresh_api_key():
                resp = self._search(normalized)
            if resp.status_code != 200:
                return Evidence(source=self.source, found=False)
            for metadata in _cosing_metadata(resp.json()):
                raw_name = _first(metadata, "inciName")
                if raw_name and normalize_name(raw_name) == normalized:
                    enrichment = {
                        "inci_name": raw_name,
                        "cas_number": _first(metadata, "casNo"),
                        "ec_number": _first(metadata, "ecNo"),
                        "substance_id": _first(metadata, "substanceId"),
                        "chemical_name": _first(metadata, "chemicalName"),
                        "description": _first(metadata, "chemicalDescription"),
                    }
                    return Evidence(
                        source=self.source,
                        found=True,
                        canonical=raw_name.title(),
                        url=COSING_SEARCH_URL,
                        confidence=COSING_CONFIDENCE,
                        enrichment={k: v for k, v in enrichment.items() if v is not None},
                    )
        except Exception:  # noqa: BLE001 - best-effort source, never fatal
            logger.debug("cosing lookup failed for %r", normalized, exc_info=True)
        return Evidence(source=self.source, found=False)

    def _search(self, normalized: str) -> httpx.Response:
        return _request_with_retry(
            self._client,
            "POST",
            COSING_SEARCH_URL,
            data={"apiKey": self._api_key, "text": f'"{normalized}"', "pageSize": "5"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def _refresh_api_key(self) -> bool:
        try:
            resp = _get_with_retry(self._client, COSING_CONFIG_URL)
            if resp.status_code != 200:
                return False
            key = _find_api_key(resp.json())
            if key:
                self._api_key = key
                return True
        except Exception:  # noqa: BLE001 - the secondary source remains available
            logger.debug("could not refresh CosIng API key", exc_info=True)
        return False


class INCIDecoderLookup:
    """Direct-slug lookup with a first-result search fallback."""

    source = "incidecoder"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or _http_client(follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def lookup(self, normalized: str) -> Evidence:
        url = INCIDECODER_URL_TEMPLATE.format(slug=slug(normalized))
        resp = _get_with_retry(self._client, url)
        canonical = _page_canonical(resp.text) if resp.status_code == 200 else None
        if not canonical or normalize_name(canonical) != normalized:
            search = _get_with_retry(
                self._client, INCIDECODER_SEARCH_URL, params={"query": normalized}
            )
            result_path = _first_ingredient_link(search.text) if search.status_code == 200 else None
            if not result_path:
                return Evidence(source=self.source, found=False, url=url)
            url = urljoin(INCIDECODER_SEARCH_URL, result_path)
            result = _get_with_retry(self._client, url)
            canonical = _page_canonical(result.text) if result.status_code == 200 else None
        if not canonical:
            return Evidence(source=self.source, found=False, url=url)
        return Evidence(
            source=self.source,
            found=True,
            canonical=canonical,
            url=url,
            confidence=INCIDECODER_CONFIDENCE,
        )


def default_lookups() -> list[Lookup]:
    return [
        CosIngSearchLookup(),
        INCIDecoderLookup(),
        PubChemLookup(),
    ]


def gather_evidence(normalized: str, lookups: list[Lookup]) -> list[Evidence]:
    """Run independent lookups concurrently; one failure never hides the rest."""
    out: list[Evidence | None] = [None] * len(lookups)
    with ThreadPoolExecutor(max_workers=max(1, len(lookups))) as executor:
        futures = {
            executor.submit(lookup.lookup, normalized): (index, lookup)
            for index, lookup in enumerate(lookups)
        }
        for future in as_completed(futures):
            index, lookup = futures[future]
            try:
                out[index] = future.result()
            except Exception:  # noqa: BLE001 - one flaky source must not fail intake
                logger.warning("%s lookup failed for %r", lookup.source, normalized, exc_info=True)
                out[index] = Evidence(source=lookup.source, found=False)
    return [ev for ev in out if ev is not None]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _http_client(follow_redirects: bool = False) -> httpx.Client:
    return httpx.Client(
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=follow_redirects,
        verify=ssl.create_default_context(cafile=certifi.where()),
    )


def _get_with_retry(
    client: httpx.Client, url: str, params: dict[str, Any] | None = None
) -> httpx.Response:
    return _request_with_retry(client, "GET", url, params=params)


def _request_with_retry(
    client: httpx.Client, method: str, url: str, **kwargs: Any
) -> httpx.Response:
    last_exc: httpx.HTTPError | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.request(method, url, **kwargs)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_exc = exc
            if attempt >= MAX_RETRIES:
                raise
            _sleep_before_retry(attempt)
            continue
        if not _should_retry_status(resp.status_code) or attempt >= MAX_RETRIES:
            return resp
        retry_after = _retry_after_seconds(resp.headers.get("retry-after"))
        if retry_after is not None and retry_after > MAX_RETRY_AFTER_SECONDS:
            return resp
        _sleep_before_retry(attempt, retry_after)
    if last_exc:
        raise last_exc
    raise RuntimeError("unreachable retry state")


def _should_retry_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code < 600


def _sleep_before_retry(attempt: int, retry_after: float | None = None) -> None:
    delay = retry_after
    if delay is None:
        delay = min(BACKOFF_SECONDS * (2**attempt), MAX_BACKOFF_SECONDS)
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


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _exact_synonym(normalized: str, synonyms: list[str]) -> str | None:
    """PubChem's exact rendering of the queried name; renderings of *other*
    synonyms are chemical names, not spellings of this token — never those."""
    for syn in synonyms:
        if normalize_name(syn) == normalized:
            return syn
    return None


def _cosing_metadata(payload: Any) -> list[dict[str, Any]]:
    results = payload.get("results", []) if isinstance(payload, dict) else []
    return [
        r["metadata"]
        for r in results
        if isinstance(r, dict) and isinstance(r.get("metadata"), dict)
    ]


def _first(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if isinstance(value, list):
        if not value:
            return None
        value = value[0]
    return str(value).strip() if value is not None and str(value).strip() else None


def _find_api_key(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower().replace("_", "").endswith("apikey") and isinstance(value, str) and value:
                return value
            found = _find_api_key(value)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _find_api_key(value)
            if found:
                return found
    return None


def _extract_h1(text: str) -> str | None:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    return _strip_html(match.group(1)) or None if match else None


def _extract_title(text: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if not match:
        return None
    title = _strip_html(match.group(1))
    title = title.split("|", 1)[0].strip()
    title = re.sub(r"\s*\(Explained \+ Products\)\s*$", "", title, flags=re.I)
    return title or None


def _strip_html(text: str) -> str:
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))).strip()


def _page_canonical(text: str) -> str | None:
    return _extract_h1(text) or _extract_title(text)


def _first_ingredient_link(text: str) -> str | None:
    match = re.search(r'href=["\']([^"\']*/ingredients/[^"\'#?]+)', text, re.I)
    return match.group(1) if match else None
