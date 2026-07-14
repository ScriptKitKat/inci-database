"""Apply stage: auto-approve decision_ready submissions, then describe.

All canonical writes happen inside the `apply_product_submission` RPC —
this stage only invokes it. `describe` batches Haiku short descriptions
for newly approved products, reusing anthropic_batch_id on the (now
approved) submission row to track the pending describe batch.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .. import db
from ..config import settings
from ..llm import batch as llm_batch
from ..llm.prompts import render

logger = logging.getLogger(__name__)


def run(limit: int | None = None) -> dict[str, int]:
    counters = {"approved": 0, "duplicate": 0, "failed": 0}
    rows = db.fetch_submissions("decision_ready", limit=limit or settings().claim_limit)
    for row in rows:
        try:
            result = db.apply_submission(row["id"])
            counters[result] = counters.get(result, 0) + 1
        except Exception as exc:  # noqa: BLE001 - isolate per submission
            logger.exception("apply failed for submission %s", row["id"])
            db.fail_submission(row["id"], f"{type(exc).__name__}: {exc}")
            counters["failed"] += 1
    return counters


def describe() -> dict[str, int]:
    counters = {"described": 0, "submitted": 0, "waiting": 0, "errored": 0}
    _poll_describe_batches(counters)
    _submit_describe_batch(counters)
    return counters


def _poll_describe_batches(counters: dict[str, int]) -> None:
    rows = db.fetch_submissions("approved", batch_id_is_null=False)
    by_batch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_batch[row["anthropic_batch_id"]].append(row)

    for batch_id, subs in by_batch.items():
        status = llm_batch.batch_status(batch_id)
        if status not in llm_batch.TERMINAL_STATUSES:
            counters["waiting"] += len(subs)
            continue
        results = dict(llm_batch.batch_results(batch_id)) if status == "ended" else {}
        for sub in subs:
            text = results.get(f"describe_{sub['id']}")
            if text and text.strip():
                db.set_product_description_if_missing(sub["product_id"], text.strip())
                counters["described"] += 1
            else:
                # Description is best-effort; the product ships without one
                # rather than blocking (a later run can resubmit).
                counters["errored"] += 1
            db.update_submission(sub["id"], {"anthropic_batch_id": None})


def _submit_describe_batch(counters: dict[str, int]) -> None:
    subs = [s for s in db.fetch_approved_needing_description() if s.get("product_id")]
    requests = []
    ids = []
    for sub in subs:
        try:
            context = db.fetch_product_description_context(sub["product_id"])
        except Exception:  # noqa: BLE001 - context fetch must not block the tick
            logger.exception("describe context failed for submission %s", sub["id"])
            counters["errored"] += 1
            continue
        requests.append(
            {"custom_id": f"describe_{sub['id']}", "params": _describe_params(sub, context)}
        )
        ids.append(sub["id"])
    if not requests:
        return
    batch_id = llm_batch.submit_batch(requests)
    for submission_id in ids:
        db.update_submission(submission_id, {"anthropic_batch_id": batch_id})
    counters["submitted"] = len(requests)


def _describe_params(sub: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    s = settings()
    lines = [
        f"- {i['inci_name']}: {', '.join(i['functions']) if i['functions'] else 'unknown'}"
        for i in context["ingredients"][:15]
        if i.get("inci_name")
    ]
    return {
        "model": s.describe_model,
        "max_tokens": s.describe_max_tokens,
        "messages": [
            {
                "role": "user",
                "content": render(
                    "product_description",
                    brand_name=context.get("brand_name") or sub["brand_name"],
                    product_name=context.get("product_name") or sub["product_name"],
                    ingredients="\n".join(lines) or "- (no matched ingredients)",
                ),
            }
        ],
    }
