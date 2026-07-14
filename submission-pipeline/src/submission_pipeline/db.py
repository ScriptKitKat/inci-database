"""Supabase access layer for the submission pipeline.

All writes flow through the service role client. Product approval writes
happen inside `apply_product_submission`; remote canonical ingredient IDs are
mirrored through a restricted RPC before staging tokens reference them.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from .config import settings

WORKER_ACTOR = "worker"


@lru_cache(maxsize=1)
def client() -> Client:
    s = settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def reset_client() -> None:
    client.cache_clear()


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------


def create_submission(
    brand_name: str,
    product_name: str,
    raw_ingredient_text: str,
    submitted_by: str | None = None,
) -> dict[str, Any]:
    res = (
        client()
        .table("product_submissions")
        .insert(
            {
                "brand_name": brand_name,
                "product_name": product_name,
                "raw_ingredient_text": raw_ingredient_text,
                "submitted_by": submitted_by,
            }
        )
        .execute()
    )
    return res.data[0]


def claim_submissions(from_status: str, to_status: str, limit: int) -> list[dict[str, Any]]:
    res = (
        client()
        .rpc(
            "claim_product_submissions",
            {"p_from_status": from_status, "p_to_status": to_status, "p_limit": limit},
        )
        .execute()
    )
    return res.data or []


def fail_submission(submission_id: str, error: str) -> None:
    client().rpc(
        "fail_product_submission",
        {
            "p_id": submission_id,
            "p_error": error,
            "p_max_attempts": settings().max_attempts,
        },
    ).execute()


def update_submission(submission_id: str, fields: dict[str, Any]) -> None:
    client().table("product_submissions").update(fields).eq("id", submission_id).execute()


def claim_verification_submissions(limit: int) -> list[dict[str, Any]]:
    res = client().rpc("claim_submission_verification", {"p_limit": limit}).execute()
    return res.data or []


def create_verification_batch(
    batch_id: str,
    submission_ids: list[str],
    request_count: int,
    payload_bytes: int,
) -> None:
    client().rpc(
        "create_submission_verification_batch",
        {
            "p_group_id": batch_id,
            "p_submission_ids": submission_ids,
            "p_request_count": request_count,
            "p_payload_bytes": payload_bytes,
        },
    ).execute()


def attach_verification_batch(batch_id: str, anthropic_batch_id: str) -> None:
    client().rpc(
        "attach_submission_verification_batch",
        {"p_group_id": batch_id, "p_anthropic_batch_id": anthropic_batch_id},
    ).execute()


def release_verification_batch(batch_id: str, error: str, *, orphaned: bool = False) -> None:
    client().rpc(
        "release_submission_verification_batch",
        {
            "p_group_id": batch_id,
            "p_error": error,
            "p_max_attempts": settings().max_attempts,
            "p_orphaned": orphaned,
        },
    ).execute()


def fetch_verification_batches(status: str) -> list[dict[str, Any]]:
    return (
        client()
        .table("submission_verification_batches")
        .select("*")
        .eq("status", status)
        .order("created_at")
        .execute()
        .data
        or []
    )


def recover_stale_verification_batches(older_than_minutes: int) -> int:
    res = client().rpc(
        "recover_stale_submission_verification",
        {
            "p_older_than_minutes": older_than_minutes,
            "p_max_attempts": settings().max_attempts,
        },
    ).execute()
    return int(res.data or 0)


def close_verification_batch(batch_id: str, status: str, error: str | None = None) -> None:
    client().table("submission_verification_batches").update(
        {"status": status, "last_error": error}
    ).eq("id", batch_id).execute()


def finalize_submission_verification(
    submission_id: str,
    expected_batch_id: str | None,
    token_updates: list[dict[str, Any]],
    verification: dict[str, Any],
    status: str,
    trigger: str | None,
) -> bool:
    res = client().rpc(
        "finalize_submission_verification",
        {
            "p_id": submission_id,
            "p_expected_batch_id": expected_batch_id,
            "p_token_updates": token_updates,
            "p_verification": verification,
            "p_status": status,
            "p_trigger": trigger,
        },
    ).execute()
    return bool(res.data)


def release_stale_claims(status: str, older_than_minutes: int) -> dict[str, int]:
    """Recover claims abandoned by a crashed worker: back to `received`,
    or `failed` once the submission has exhausted its attempts."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)).isoformat()
    failed = (
        client()
        .table("product_submissions")
        .update({"status": "failed", "locked_at": None, "last_error": "stale claim released"})
        .eq("status", status)
        .lt("locked_at", cutoff)
        .gte("attempt_count", settings().max_attempts)
        .execute()
    )
    released = (
        client()
        .table("product_submissions")
        .update({"status": "received", "locked_at": None})
        .eq("status", status)
        .lt("locked_at", cutoff)
        .execute()
    )
    return {"released": len(released.data or []), "failed": len(failed.data or [])}


def fetch_submissions(
    status: str,
    *,
    batch_id_is_null: bool | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    q = client().table("product_submissions").select("*").eq("status", status)
    if batch_id_is_null is True:
        q = q.is_("anthropic_batch_id", "null")
    elif batch_id_is_null is False:
        q = q.not_.is_("anthropic_batch_id", "null")
    q = q.order("created_at")
    if limit is not None:
        q = q.limit(limit)
    return q.execute().data or []


def apply_submission(submission_id: str, actor: str = WORKER_ACTOR) -> str:
    res = (
        client()
        .rpc("apply_product_submission", {"p_id": submission_id, "p_actor": actor})
        .execute()
    )
    return str(res.data)


def purge_stale(days: int) -> int:
    res = client().rpc("purge_stale_submissions", {"p_days": days}).execute()
    return int(res.data or 0)


def audit(submission_id: str, action: str, payload: dict[str, Any] | None = None) -> None:
    client().table("submission_audit").insert(
        {
            "submission_id": submission_id,
            "action": action,
            "actor": WORKER_ACTOR,
            "payload": payload or {},
        }
    ).execute()


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


def replace_tokens(submission_id: str, rows: list[dict[str, Any]]) -> None:
    """Idempotent intake write: retries reparse from scratch, so stale rows
    from a previous attempt must not linger."""
    client().table("submission_tokens").delete().eq("submission_id", submission_id).execute()
    if rows:
        client().table("submission_tokens").insert(rows).execute()


def fetch_tokens(submission_id: str) -> list[dict[str, Any]]:
    res = (
        client()
        .table("submission_tokens")
        .select("*")
        .eq("submission_id", submission_id)
        .order("position")
        .execute()
    )
    return res.data or []


def update_token(token_id: str, fields: dict[str, Any]) -> None:
    client().table("submission_tokens").update(fields).eq("id", token_id).execute()


# ---------------------------------------------------------------------------
# Catalog reads (verification context only; never writes)
# ---------------------------------------------------------------------------


def find_product_formula_match(
    tokens: list[str], brand_name: str, product_name: str, similarity_threshold: float
) -> dict[str, Any] | None:
    res = (
        client()
        .rpc(
            "find_product_formula_match",
            {
                "p_tokens": tokens,
                "p_brand_name": brand_name,
                "p_product_name": product_name,
                "p_similarity_threshold": similarity_threshold,
            },
        )
        .execute()
    )
    return res.data[0] if res.data else None


def find_product_by_identity(brand_name: str, product_name: str) -> dict[str, Any] | None:
    res = (
        client()
        .rpc(
            "find_product_by_identity",
            {"p_brand_name": brand_name, "p_product_name": product_name},
        )
        .execute()
    )
    return res.data[0] if res.data else None


def fetch_ingredient(ingredient_id: str) -> dict[str, Any] | None:
    res = (
        client()
        .table("ingredients")
        .select("id, inci_name, normalized_name")
        .eq("id", ingredient_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def sync_remote_catalog_ingredient(ingredient: dict[str, Any]) -> str:
    res = (
        client()
        .rpc(
            "sync_remote_catalog_ingredient",
            {
                "p_id": ingredient["id"],
                "p_inci_name": ingredient["inci_name"],
                "p_slug": ingredient["slug"],
            },
        )
        .execute()
    )
    return str(res.data)


def fetch_brand_product_domains(submission_id: str) -> list[str]:
    submission = (
        client()
        .table("product_submissions")
        .select("brand_name")
        .eq("id", submission_id)
        .single()
        .execute()
        .data
    )
    if not submission:
        return []
    rows = (
        client()
        .table("brand_product_domains")
        .select("domain")
        .eq("normalized_brand_name", str(submission["brand_name"]).strip().upper())
        .execute()
        .data
        or []
    )
    return [str(row["domain"]) for row in rows]


def fetch_approved_needing_description(limit: int = 50) -> list[dict[str, Any]]:
    res = (
        client()
        .table("product_submissions")
        .select("*, products!inner(short_description)")
        .eq("status", "approved")
        .is_("anthropic_batch_id", "null")
        .is_("products.short_description", "null")
        .limit(limit)
        .execute()
    )
    return res.data or []


def fetch_product_description_context(product_id: str) -> dict[str, Any]:
    product = (
        client()
        .table("products")
        .select("id, name, short_description, brands(name)")
        .eq("id", product_id)
        .single()
        .execute()
        .data
    )
    rows = (
        client()
        .table("product_ingredients")
        .select("position, ingredients(inci_name, ingredient_information(functions))")
        .eq("product_id", product_id)
        .not_.is_("ingredient_id", "null")
        .order("position")
        .execute()
        .data
        or []
    )
    ingredients = []
    for row in rows:
        ing = row.get("ingredients") or {}
        info = ing.get("ingredient_information") or {}
        if isinstance(info, list):
            info = info[0] if info else {}
        ingredients.append(
            {
                "inci_name": ing.get("inci_name"),
                "functions": info.get("functions") or [],
            }
        )
    return {
        "product_name": product["name"],
        "brand_name": (product.get("brands") or {}).get("name"),
        "short_description": product.get("short_description"),
        "ingredients": ingredients,
    }


def set_product_description_if_missing(product_id: str, description: str) -> None:
    client().table("products").update({"short_description": description}).eq("id", product_id).is_(
        "short_description", "null"
    ).execute()
