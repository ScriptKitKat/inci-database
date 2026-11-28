from __future__ import annotations

import json
import uuid
from collections import defaultdict
from typing import Any

from anthropic import APIError as AnthropicError
from httpx import HTTPError
from postgrest.exceptions import APIError as DatabaseError

from .. import db
from ..config import settings
from ..enrichment import parse_enrichment, review_reason
from ..llm import batch as llm_batch
from ..llm.prompts import render

ENRICHMENT_ERRORS = (
    AnthropicError,
    HTTPError,
    DatabaseError,
    ValueError,
    TypeError,
    KeyError,
    RuntimeError,
)


def build_request(row: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    s = settings()
    return {
        "custom_id": f"enrich_{row['ingredient_id']}",
        "params": {
            "model": s.describe_model,
            "max_tokens": s.enrich_max_tokens,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "user",
                    "content": render(
                        "enrich_ingredient", context=json.dumps(context, ensure_ascii=False)
                    ),
                }
            ],
        },
    }


def run() -> dict[str, int]:
    s = settings()
    counters = {"submitted": 0, "applied": 0, "review": 0, "waiting": 0, "failed": 0}
    batches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in db.fetch_enrichment_batches():
        batches[row["anthropic_batch_id"]].append(row)
    for batch_id, rows in batches.items():
        try:
            status = llm_batch.batch_status(batch_id)
            if status not in llm_batch.TERMINAL_STATUSES:
                counters["waiting"] += len(rows)
                continue
            results = dict(llm_batch.batch_results(batch_id)) if status == "ended" else {}
        except ENRICHMENT_ERRORS:
            counters["waiting"] += len(rows)
            continue
        for row in rows:
            try:
                text = results.get(f"enrich_{row['ingredient_id']}")
                if text is None:
                    db.fail_enrichment(row, "enrichment_batch_failed")
                    counters["failed"] += 1
                    continue
                context = db.fetch_enrichment_context(row["ingredient_id"])
                result = parse_enrichment(text, context["allowed_functions"])
                reason = review_reason(result, s.enrich_confidence_threshold)
                if reason:
                    db.review_enrichment(row, reason)
                    counters["review"] += 1
                else:
                    status = db.apply_enrichment(row, result.model_dump())
                    counters["review" if status == "pending_human" else "applied"] += 1
            except ENRICHMENT_ERRORS:
                db.fail_enrichment(row, "enrichment_result_processing_failed")
                counters["failed"] += 1
    claim_id = str(uuid.uuid4())
    rows = db.claim_enrichment(claim_id, s.enrich_claim_limit)
    requests = []
    for row in rows:
        try:
            requests.append(build_request(row, db.fetch_enrichment_context(row["ingredient_id"])))
        except ENRICHMENT_ERRORS:
            db.fail_enrichment(row, "enrichment_context_failed")
            counters["failed"] += 1
    if requests:
        try:
            batch_id = llm_batch.submit_batch(requests)
            db.attach_enrichment_batch(claim_id, batch_id, len(requests))
            counters["submitted"] = len(requests)
        except ENRICHMENT_ERRORS:
            for row in rows:
                db.fail_enrichment(row, "enrichment_batch_submission_failed")
            counters["failed"] += len(requests)
    return counters
