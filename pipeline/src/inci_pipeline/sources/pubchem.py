"""PubChem REST client.

Lookup flow per ingredient:
  /compound/xref/RN/{cas}/cids/JSON      -> compound id
  /compound/cid/{cid}/synonyms/JSON      -> synonym list
  /compound/cid/{cid}/property/IUPACName  -> IUPAC

`xref/RN` is the documented namespace for CAS Registry Numbers. The
shorter `cas/{cas}/...` form is not a real namespace and returns 400.

PubChem allows ~5 req/sec without an API key.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Self

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PubChemRecord:
    cid: int
    iupac_name: str | None
    synonyms: list[str]


class PubChemClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=10.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=5),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
    )
    def lookup_by_cas(self, cas: str) -> PubChemRecord | None:
        cids = self._client.get(f"{BASE}/compound/xref/RN/{cas}/cids/JSON")
        # 400 or 404 = no compound for this CAS; treat as "skip", don't retry
        if cids.status_code in (400, 404):
            return None
        if cids.status_code >= 500:
            cids.raise_for_status()
        if cids.status_code != 200:
            return None
        cid_list = cids.json().get("IdentifierList", {}).get("CID", [])
        if not cid_list:
            return None
        cid = cid_list[0]

        syn = self._client.get(f"{BASE}/compound/cid/{cid}/synonyms/JSON")
        if syn.status_code == 200:
            synonyms = (
                syn.json()
                .get("InformationList", {})
                .get("Information", [{}])[0]
                .get("Synonym", [])
            )
        else:
            synonyms = []

        iupac = None
        props = self._client.get(f"{BASE}/compound/cid/{cid}/property/IUPACName/JSON")
        if props.status_code == 200:
            try:
                iupac = (
                    props.json()
                    .get("PropertyTable", {})
                    .get("Properties", [{}])[0]
                    .get("IUPACName")
                )
            except Exception:
                log.debug("Could not read optional IUPAC name for CID %s", cid, exc_info=True)

        return PubChemRecord(cid=cid, iupac_name=iupac, synonyms=synonyms[:50])
