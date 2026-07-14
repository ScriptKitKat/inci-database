"""Supabase client and typed upsert helpers.

All writes flow through the service role client, which bypasses RLS.
Public-read clients are not used by the pipeline.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel
from supabase import Client, create_client

from .config import settings

RunStatus = Literal["running", "success", "failed"]


class IngredientRow(BaseModel):
    inci_name: str
    slug: str
    cas_number: str | None = None
    ec_number: str | None = None
    iupac_name: str | None = None
    ph_eur_name: str | None = None
    is_restricted_eu: bool = False
    is_restricted_us: bool = False
    function_tags: list[str] = []
    skin_type_tag: list[str] = []
    concern_tag: list[str] = []


class AliasRow(BaseModel):
    ingredient_id: UUID
    alias: str
    alias_type: str = "synonym"
    language: str = "en"
    source: str = "manual"


class SourceRow(BaseModel):
    ingredient_id: UUID
    source_type: str
    external_id: str | None = None
    url: str | None = None
    title: str | None = None
    raw_payload: dict[str, Any] | None = None


@lru_cache(maxsize=1)
def client() -> Client:
    s = settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def reset_client() -> None:
    """Drop the cached Supabase client so long import runs open a fresh connection."""
    client.cache_clear()


def _chunked(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def upsert_ingredients(
    rows: Sequence[IngredientRow], chunk: int = 500
) -> dict[str, UUID]:
    """Upsert ingredients and return a {inci_name: id} map built from
    the PostgREST representation response. Callers should use this map
    instead of issuing a follow-up SELECT per row — at >10k rows the
    fetch loop will saturate Supabase's HTTP/2 stream limit and the
    connection gets terminated."""
    out: dict[str, UUID] = {}
    if not rows:
        return out
    for batch in _chunked(rows, chunk):
        payload = [
            {"inci_name": r.inci_name, "slug": r.slug}
            for r in batch
        ]
        res = (
            client()
            .table("ingredients")
            .upsert(payload, on_conflict="inci_name")
            .execute()
        )
        for row in res.data or []:
            out[row["inci_name"]] = UUID(row["id"])
        ingredient_ids = [row["id"] for row in res.data or []]
        existing_information = {}
        if ingredient_ids:
            existing = (
                client()
                .table("ingredient_information")
                .select(
                    "ingredient_id,functions,cosing_information,additional_information"
                )
                .in_("ingredient_id", ingredient_ids)
                .execute()
            )
            existing_information = {
                row["ingredient_id"]: row for row in existing.data or []
            }
        information_payload = []
        by_name = {r.inci_name: r for r in batch}
        for row in res.data or []:
            source = by_name[row["inci_name"]]
            current = existing_information.get(row["id"], {})
            cosing_update = {
                key: value
                for key, value in {
                    "cas_number": source.cas_number,
                    "ec_number": source.ec_number,
                    "iupac_name": source.iupac_name,
                    "ph_eur_name": source.ph_eur_name,
                }.items()
                if value is not None
            }
            additional_update: dict[str, Any] = {}
            if source.skin_type_tag:
                additional_update["skin_type_tags"] = source.skin_type_tag
            if source.concern_tag:
                additional_update["concern_tags"] = source.concern_tag
            if source.is_restricted_eu:
                additional_update["is_restricted_eu"] = True
            if source.is_restricted_us:
                additional_update["is_restricted_us"] = True
            information_payload.append(
                {
                    "ingredient_id": row["id"],
                    "functions": source.function_tags or current.get("functions") or [],
                    "cosing_information": {
                        **(current.get("cosing_information") or {}),
                        **cosing_update,
                    },
                    "additional_information": {
                        **(current.get("additional_information") or {}),
                        **additional_update,
                    },
                }
            )
        if information_payload:
            client().table("ingredient_information").upsert(
                information_payload, on_conflict="ingredient_id"
            ).execute()
    return out


def upsert_aliases(rows: Sequence[AliasRow], chunk: int = 1000) -> int:
    if not rows:
        return 0
    total = 0
    for batch in _chunked(rows, chunk):
        payload = [r.model_dump(mode="json") for r in batch]
        client().table("ingredient_aliases").upsert(
            payload, on_conflict="ingredient_id,alias,language"
        ).execute()
        total += len(batch)
    return total


def upsert_sources(rows: Sequence[SourceRow], chunk: int = 500) -> int:
    if not rows:
        return 0
    total = 0
    for batch in _chunked(rows, chunk):
        payload = [r.model_dump(mode="json") for r in batch]
        client().table("ingredient_sources").upsert(
            payload, on_conflict="ingredient_id,source_type,external_id"
        ).execute()
        total += len(batch)
    return total


def fetch_ingredient_id(inci_name: str) -> UUID | None:
    res = (
        client()
        .table("ingredients")
        .select("id")
        .eq("inci_name", inci_name)
        .limit(1)
        .execute()
    )
    if res.data:
        return UUID(res.data[0]["id"])
    return None


def stream_ingredients_with_cas(page_size: int = 1000) -> Iterable[dict[str, Any]]:
    offset = 0
    while True:
        res = (
            client()
            .table("ingredient_information")
            .select("ingredient_id, cosing_information, ingredients(inci_name)")
            .not_.is_("cosing_information->>cas_number", "null")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return
        for row in rows:
            cosing = row.get("cosing_information") or {}
            ingredient = row.get("ingredients") or {}
            yield {
                "id": row["ingredient_id"],
                "inci_name": ingredient.get("inci_name"),
                "cas_number": cosing.get("cas_number"),
                "ec_number": cosing.get("ec_number"),
            }
        if len(rows) < page_size:
            return
        offset += page_size


def fetch_normalized_match_terms(page_size: int = 1000) -> set[str]:
    """Return normalized ingredient and alias terms for label tokenization.

    The product importer uses this to segment malformed all-caps labels that
    omit commas, preferring the longest known INCI/alias phrase.
    """
    terms: set[str] = set()
    offset = 0
    while True:
        res = (
            client()
            .table("ingredients")
            .select("normalized_name")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            if row.get("normalized_name"):
                terms.add(row["normalized_name"])
        if len(rows) < page_size:
            break
        offset += page_size

    offset = 0
    while True:
        res = (
            client()
            .table("ingredient_aliases")
            .select("normalized_alias")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            if row.get("normalized_alias"):
                terms.add(row["normalized_alias"])
        if len(rows) < page_size:
            break
        offset += page_size
    return terms


def fetch_exact_match_index(page_size: int = 1000) -> dict[str, UUID]:
    """Return a normalized token -> ingredient id index for fast product imports."""
    index: dict[str, UUID] = {}
    offset = 0
    while True:
        res = (
            client()
            .table("ingredients")
            .select("id, normalized_name")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            if row.get("normalized_name"):
                index.setdefault(row["normalized_name"], UUID(row["id"]))
        if len(rows) < page_size:
            break
        offset += page_size

    offset = 0
    while True:
        res = (
            client()
            .table("ingredient_aliases")
            .select("ingredient_id, normalized_alias")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            if row.get("normalized_alias"):
                index.setdefault(row["normalized_alias"], UUID(row["ingredient_id"]))
        if len(rows) < page_size:
            break
        offset += page_size
    return index


def fetch_existing_product_slugs(page_size: int = 1000) -> set[str]:
    """Return product slugs that already have ingredient rows.

    Interrupted imports can leave a product row behind before its ingredients
    are inserted. Those slugs are intentionally not skipped on resume.
    """
    product_ids_with_ingredients: set[str] = set()
    offset = 0
    while True:
        res = (
            client()
            .table("product_ingredients")
            .select("product_id")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            if row.get("product_id"):
                product_ids_with_ingredients.add(row["product_id"])
        if len(rows) < page_size:
            break
        offset += page_size

    slugs: set[str] = set()
    offset = 0
    while True:
        res = (
            client()
            .table("products")
            .select("id, slug")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            if row.get("id") in product_ids_with_ingredients and row.get("slug"):
                slugs.add(row["slug"])
        if len(rows) < page_size:
            break
        offset += page_size
    return slugs


def _fetch_curated_ids() -> list[UUID]:
    """All ingredient ids in the curation queue, ordered by priority."""
    out: list[UUID] = []
    offset = 0
    page = 500
    while True:
        res = (
            client()
            .table("ingredient_curation_queue")
            .select("ingredient_id")
            .order("priority")
            .range(offset, offset + page - 1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            break
        out.extend(UUID(r["ingredient_id"]) for r in rows)
        if len(rows) < page:
            break
        offset += page
    return out


def stream_curated_ingredients(
    require_cas: bool = False, page_size: int = 200
) -> Iterable[dict[str, Any]]:
    """Stream ingredients flagged in the curation queue.

    Used by the expensive stages (PubMed abstract fetch, Claude
    editorial generation) to limit work to a curated subset by
    default. Pass `require_cas=True` to additionally filter to
    ingredients that have a CAS number (needed by PubMed lookups).
    """
    ids = _fetch_curated_ids()
    if not ids:
        return
    for i in range(0, len(ids), page_size):
        batch = ids[i : i + page_size]
        q = client().table("ingredients").select(
            "id, inci_name, ingredient_information(cosing_information)"
        )
        q = q.in_("id", [str(uid) for uid in batch])
        if require_cas:
            q = q.not_.is_("ingredient_information.cosing_information->>cas_number", "null")
        res = q.execute()
        for row in res.data or []:
            info = row.pop("ingredient_information", None) or {}
            cosing = info.get("cosing_information") or {}
            row["cas_number"] = cosing.get("cas_number")
            yield row


def fetch_ingredients_for_editorial(
    ingredient_ids: list[UUID], page_size: int = 200
) -> Iterable[dict[str, Any]]:
    """Same as stream_curated_ingredients but returns the extra fields
    the editorial prompt needs (function tags, restrictions)."""
    for i in range(0, len(ingredient_ids), page_size):
        batch = ingredient_ids[i : i + page_size]
        res = (
            client()
            .table("ingredients")
            .select(
                "id, inci_name, "
                "ingredient_information(functions,additional_information)"
            )
            .in_("id", [str(uid) for uid in batch])
            .execute()
        )
        for row in res.data or []:
            info = row.pop("ingredient_information", None) or {}
            additional = info.get("additional_information") or {}
            row["function_tags"] = info.get("functions") or []
            row["is_restricted_eu"] = additional.get("is_restricted_eu", False)
            row["is_restricted_us"] = additional.get("is_restricted_us", False)
            yield row


def patch_ingredient_information(
    ingredient_id: UUID, *, cosing: dict[str, Any] | None = None,
    additional: dict[str, Any] | None = None
) -> None:
    """Merge selected JSON fields without erasing information from other stages."""
    current = (
        client()
        .table("ingredient_information")
        .select("cosing_information,additional_information")
        .eq("ingredient_id", str(ingredient_id))
        .single()
        .execute()
        .data
    )
    update: dict[str, Any] = {}
    if cosing:
        update["cosing_information"] = {
            **(current.get("cosing_information") or {}),
            **cosing,
        }
    if additional:
        update["additional_information"] = {
            **(current.get("additional_information") or {}),
            **additional,
        }
    if update:
        client().table("ingredient_information").update(update).eq(
            "ingredient_id", str(ingredient_id)
        ).execute()


@contextmanager
def ingestion_run(stage: str, metadata: dict[str, Any] | None = None):
    """Wrap a stage in an ingestion_runs audit row."""
    insert = (
        client()
        .table("ingestion_runs")
        .insert(
            {
                "stage": stage,
                "status": "running",
                "metadata": metadata or {},
            }
        )
        .execute()
    )
    run_id = insert.data[0]["id"]
    counters = {"rows_in": 0, "rows_upserted": 0}
    try:
        yield counters
        client().table("ingestion_runs").update(
            {
                "status": "success",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "rows_in": counters["rows_in"],
                "rows_upserted": counters["rows_upserted"],
            }
        ).eq("id", run_id).execute()
    except Exception as exc:
        client().table("ingestion_runs").update(
            {
                "status": "failed",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "rows_in": counters["rows_in"],
                "rows_upserted": counters["rows_upserted"],
                "error": f"{type(exc).__name__}: {exc}"[:2000],
            }
        ).eq("id", run_id).execute()
        raise


def last_successful_run(stage: str) -> datetime | None:
    res = (
        client()
        .table("ingestion_runs")
        .select("finished_at")
        .eq("stage", stage)
        .eq("status", "success")
        .order("finished_at", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    return datetime.fromisoformat(res.data[0]["finished_at"])
