from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from anthropic import Anthropic

from ..config import settings
from ..db import client
from .decisions import parse_llm_decision, review_status_for


def submit_batch(
    run_id: UUID,
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str | None:
    items = _pending_items(run_id)
    if not items:
        return None

    batch_row = (
        client()
        .table("ingredient_llm_batches")
        .insert(
            {
                "run_id": str(run_id),
                "status": "created",
                "request_count": len(items),
            }
        )
        .execute()
    ).data[0]
    local_batch_id = batch_row["id"]

    requests = []
    db_items = []
    for item in items:
        custom_id = f"ingredient_candidate:{item['candidate_id']}"
        payload = _request_payload(
            item,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        requests.append({"custom_id": custom_id, "params": payload})
        db_items.append(
            {
                "batch_id": local_batch_id,
                "candidate_id": item["candidate_id"],
                "custom_id": custom_id,
                "request_payload": payload,
                "status": "submitted",
            }
        )

    anthropic_batch = _anthropic().messages.batches.create(requests=requests)
    anthropic_batch_id = _get(anthropic_batch, "id")
    client().table("ingredient_llm_batch_items").insert(db_items).execute()
    client().table("ingredient_llm_batches").update(
        {
            "anthropic_batch_id": anthropic_batch_id,
            "status": "submitted",
            "submitted_at": _now_iso(),
            "raw_payload": _to_jsonable(anthropic_batch),
        }
    ).eq("id", local_batch_id).execute()
    return str(anthropic_batch_id)


def retrieve_batch(anthropic_batch_id: str) -> dict[str, Any]:
    batch_rows = (
        client()
        .table("ingredient_llm_batches")
        .select("id, run_id")
        .eq("anthropic_batch_id", anthropic_batch_id)
        .limit(1)
        .execute()
    ).data
    if not batch_rows:
        raise RuntimeError(f"unknown Anthropic batch id: {anthropic_batch_id}")
    batch = batch_rows[0]
    local_batch_id = batch["id"]

    sdk = _anthropic()
    remote_batch = sdk.messages.batches.retrieve(anthropic_batch_id)
    status = _get(remote_batch, "processing_status") or _get(remote_batch, "status") or "processing"
    if status not in {"ended", "failed", "canceled", "expired"}:
        client().table("ingredient_llm_batches").update(
            {"status": "processing", "raw_payload": _to_jsonable(remote_batch)}
        ).eq("id", local_batch_id).execute()
        return {"status": "processing", "processed": 0}

    valid_targets = _valid_target_ids()
    processed = 0
    succeeded = 0
    errored = 0
    for result in sdk.messages.batches.results(anthropic_batch_id):
        custom_id = str(_get(result, "custom_id"))
        raw_payload = _to_jsonable(result)
        item_rows = (
            client()
            .table("ingredient_llm_batch_items")
            .select("id, candidate_id")
            .eq("batch_id", local_batch_id)
            .eq("custom_id", custom_id)
            .limit(1)
            .execute()
        ).data
        if not item_rows:
            continue
        item = item_rows[0]
        text = _result_text(result)
        if text is None:
            errored += 1
            client().table("ingredient_llm_batch_items").update(
                {
                    "status": "errored",
                    "response_payload": raw_payload,
                    "error": "missing successful message text",
                }
            ).eq("id", item["id"]).execute()
            continue
        decision = parse_llm_decision(text, valid_targets)
        _upsert_llm_decision(
            run_id=UUID(batch["run_id"]),
            candidate_id=UUID(item["candidate_id"]),
            decision=decision,
        )
        client().table("ingredient_llm_batch_items").update(
            {
                "status": "succeeded",
                "response_payload": raw_payload,
            }
        ).eq("id", item["id"]).execute()
        processed += 1
        succeeded += 1

    client().table("ingredient_llm_batches").update(
        {
            "status": "retrieved",
            "succeeded_count": succeeded,
            "errored_count": errored,
            "retrieved_at": _now_iso(),
            "raw_payload": _to_jsonable(remote_batch),
        }
    ).eq("id", local_batch_id).execute()
    return {"status": status, "processed": processed, "errored": errored}


def _pending_items(run_id: UUID) -> list[dict[str, Any]]:
    decisions = (
        client()
        .table("ingredient_curation_decisions")
        .select("candidate_id")
        .eq("run_id", str(run_id))
        .eq("decision", "needs_human")
        .eq("review_status", "pending_human")
        .execute()
    ).data or []
    candidate_ids = [row["candidate_id"] for row in decisions]
    if not candidate_ids:
        return []
    candidates = (
        client()
        .table("ingredient_name_candidates")
        .select("id, source_ingredient_id, inci_name, normalized_name")
        .in_("id", candidate_ids)
        .execute()
    ).data or []
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        evidence = (
            client()
            .table("ingredient_name_evidence")
            .select("source, lookup_type, found, canonical_name, normalized_canonical, url, confidence, raw_payload")
            .eq("candidate_id", candidate["id"])
            .execute()
        ).data or []
        edges = (
            client()
            .table("ingredient_name_edges")
            .select("target_ingredient_id, target_normalized_name, relationship_type, pg_trgm_similarity, edit_distance, token_overlap, score_margin")
            .eq("candidate_id", candidate["id"])
            .execute()
        ).data or []
        out.append({**candidate, "candidate_id": candidate["id"], "evidence": evidence, "edges": edges})
    return out


def _request_payload(
    item: dict[str, Any],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    s = settings()
    prompt = {
        "task": "Decide whether a normalized cosmetic ingredient candidate should be kept, merged, aliased, rejected/quarantined, or sent to human review.",
        "rules": [
            "Use only the provided normalized-name evidence.",
            "Do not merge close-but-distinct INCI variants.",
            "Return only JSON matching the requested schema.",
        ],
        "schema": {
            "decision": "keep | merge_into_existing | alias_to_existing | reject_or_quarantine | needs_human",
            "target_ingredient_id": "uuid or null",
            "canonical_inci_name": "string or null",
            "aliases_to_add": ["string"],
            "confidence": 0.0,
            "reason": "string",
        },
        "candidate": item,
    }
    return {
        "model": model or s.ingredient_judge_model,
        "max_tokens": max_tokens or s.ingredient_judge_max_tokens,
        "temperature": s.ingredient_judge_temperature if temperature is None else temperature,
        "messages": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}],
    }


def _upsert_llm_decision(
    *,
    run_id: UUID,
    candidate_id: UUID,
    decision,
) -> None:
    candidate = (
        client()
        .table("ingredient_name_candidates")
        .select("queue_id, source_ingredient_id")
        .eq("id", str(candidate_id))
        .limit(1)
        .execute()
    ).data[0]
    client().table("ingredient_curation_decisions").upsert(
        {
            "run_id": str(run_id),
            "queue_id": candidate["queue_id"],
            "candidate_id": str(candidate_id),
            "source_ingredient_id": candidate["source_ingredient_id"],
            "target_ingredient_id": (
                str(decision.target_ingredient_id) if decision.target_ingredient_id else None
            ),
            "decision": decision.decision,
            "review_status": review_status_for(decision),
            "decision_source": "llm_batch",
            "canonical_inci_name": decision.canonical_inci_name,
            "aliases_to_add": decision.aliases_to_add,
            "confidence": decision.confidence,
            "reason": decision.reason,
        },
        on_conflict="run_id,candidate_id,decision_source",
    ).execute()


def _valid_target_ids() -> set[UUID]:
    rows = client().table("ingredients").select("id").execute().data or []
    return {UUID(row["id"]) for row in rows}


def _anthropic() -> Anthropic:
    s = settings()
    if not s.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return Anthropic(api_key=s.anthropic_api_key)


def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _result_text(result: Any) -> str | None:
    result_payload = _get(result, "result")
    if _get(result_payload, "type") not in {None, "succeeded"}:
        return None
    message = _get(result_payload, "message") or result_payload
    content = _get(message, "content") or []
    first = content[0] if content else None
    return _get(first, "text")


def _to_jsonable(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):
        return obj.dict()
    return {"repr": repr(obj)}


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now().astimezone().isoformat()
