"""Supabase access layer for the submission pipeline.

All writes flow through the service role client. Canonical-table writes
happen exclusively inside the `apply_product_submission` RPC; this module
only touches submission staging tables and worker RPCs.
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


def assign_batch_id(submission_id: str, batch_id: str) -> bool:
    """Attach a batch id only if none is set; False means another worker won."""
    res = (
        client()
        .table("product_submissions")
        .update({"anthropic_batch_id": batch_id})
        .eq("id", submission_id)
        .is_("anthropic_batch_id", "null")
        .execute()
    )
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
