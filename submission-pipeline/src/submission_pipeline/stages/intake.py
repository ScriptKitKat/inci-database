"""Intake stage.

Claims `received` submissions: tokenize the label, compare it directly
against catalog formulas, resolve each token deterministically where possible
(match_ingredient exact, then authoritative-source evidence mapping to an
existing ingredient), and queue the rest for LLM verification.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from .. import db, matching
from .. import evidence as evidence_mod
from ..config import settings
from ..models import Evidence
from ..normalize import normalize_name, tokenize_label

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _lookups() -> list[evidence_mod.Lookup]:
    return evidence_mod.default_lookups()


def reset_lookups() -> None:
    _lookups.cache_clear()


def run(limit: int | None = None) -> dict[str, int]:
    counters = {
        "claimed": 0,
        "queued": 0,
        "duplicates": 0,
        "human_review": 0,
        "failed": 0,
        "stale_released": 0,
        "stale_failed": 0,
    }
    reaped = db.release_stale_claims("triaging", settings().stale_claim_minutes)
    counters["stale_released"] = reaped["released"]
    counters["stale_failed"] = reaped["failed"]
    rows = db.claim_submissions("received", "triaging", limit or settings().claim_limit)
    counters["claimed"] = len(rows)
    for row in rows:
        try:
            _process(row, counters)
        except Exception as exc:  # noqa: BLE001 - one bad submission must not stop the tick
            logger.exception("intake failed for submission %s", row["id"])
            db.fail_submission(row["id"], f"{type(exc).__name__}: {exc}")
            counters["failed"] += 1
    return counters


def _process(row: dict[str, Any], counters: dict[str, int]) -> None:
    submission_id = row["id"]
    tokens = tokenize_label(row["raw_ingredient_text"])
    if not tokens:
        db.fail_submission(submission_id, "no ingredient tokens parsed from label")
        counters["failed"] += 1
        return

    formula_match = db.find_product_formula_match(
        tokens,
        row["brand_name"],
        row["product_name"],
        settings().product_formula_similarity_threshold,
    )
    if formula_match and formula_match["is_exact"] and formula_match["same_product"]:
        existing_product_id = formula_match["product_id"]
        db.update_submission(
            submission_id,
            {
                "status": "duplicate",
                "product_id": existing_product_id,
                "processed_at": _now_iso(),
                "locked_at": None,
            },
        )
        db.audit(submission_id, "duplicate", {"existing_product_id": existing_product_id})
        counters["duplicates"] += 1
        return

    token_rows = [_build_token_row(submission_id, pos, raw) for pos, raw in enumerate(tokens, 1)]

    # Same brand + product name already in the catalog but the formula is not
    # an exact duplicate: a human decides (reformulation vs. bad tokenization)
    # instead of apply silently creating a second product with this identity.
    identity = db.find_product_by_identity(row["brand_name"], row["product_name"])
    if identity:
        existing = {
            "product_id": identity["product_id"],
            "similarity": formula_match["similarity"] if formula_match else None,
        }
        db.replace_tokens(submission_id, token_rows)
        db.update_submission(
            submission_id,
            {
                "status": "pending_human",
                "verification": {
                    "verdict": "same_name_different_formula",
                    "existing_product": existing,
                },
                "locked_at": None,
            },
        )
        db.audit(
            submission_id,
            "pending_human",
            {"trigger": "same_name_different_formula", **existing},
        )
        counters["human_review"] += 1
        return

    if formula_match and not formula_match["product_name_matches"]:
        candidate = {
            "product_id": formula_match["product_id"],
            "similarity": formula_match["similarity"],
        }
        db.replace_tokens(submission_id, token_rows)
        db.update_submission(
            submission_id,
            {
                "status": "pending_human",
                "verification": {
                    "verdict": "similar_product",
                    "similar_product": candidate,
                },
                "locked_at": None,
            },
        )
        db.audit(
            submission_id,
            "pending_human",
            {"trigger": "similar_product", **candidate},
        )
        counters["human_review"] += 1
        return

    for token_row in token_rows:
        if token_row["resolution"] == "unresolved":
            _attach_evidence(token_row)

    db.replace_tokens(submission_id, token_rows)
    db.update_submission(
        submission_id,
        {
            "status": "verifying",
            "locked_at": None,
        },
    )
    resolved = sum(1 for t in token_rows if t["resolution"] == "matched")
    db.audit(
        submission_id,
        "intake",
        {"tokens": len(token_rows), "resolved_deterministically": resolved},
    )
    counters["queued"] += 1


def _build_token_row(submission_id: str, position: int, raw_token: str) -> dict[str, Any]:
    match = matching.match_token(raw_token)
    exact = match is not None and match.confidence >= settings().exact_match_confidence
    return {
        "submission_id": submission_id,
        "position": position,
        "raw_token": raw_token,
        "normalized_token": normalize_name(raw_token),
        "matched_ingredient_id": str(match.ingredient_id) if match else None,
        "match_type": match.match_type if match else None,
        "match_confidence": match.confidence if match else None,
        "resolution": "matched" if exact else "unresolved",
        "resolution_source": "exact_match" if exact else None,
        "evidence": [],
    }


def _attach_evidence(token_row: dict[str, Any]) -> None:
    gathered = evidence_mod.gather_evidence(token_row["normalized_token"], _lookups())
    token_row["evidence"] = [ev.to_json() for ev in gathered if ev.found]
    if evidence_mod.has_spelling_disagreement(token_row["evidence"]):
        token_row["resolution"] = "pending_human"
        db.audit(
            token_row["submission_id"],
            "token_escalated",
            {"position": token_row["position"], "trigger": "source_disagreement"},
        )
        return
    ingredient_id = _deterministic_ingredient(gathered, token_row["raw_token"])
    if ingredient_id:
        token_row.update(
            {
                "matched_ingredient_id": ingredient_id,
                "match_type": None,
                "match_confidence": None,
                "resolution": "matched",
                "resolution_source": "deterministic",
            }
        )


def _deterministic_ingredient(gathered: list[Evidence], raw_token: str = "") -> str | None:
    """An exact authoritative hit whose canonical maps to an existing
    ingredient resolves without the LLM (e.g. a CosIng synonym -> catalog)."""
    for ev in gathered:
        if not ev.found or not ev.canonical or ev.source not in evidence_mod.SPELLING_SOURCES:
            continue
        if re.findall(r"\d+", raw_token) != re.findall(r"\d+", ev.canonical):
            continue
        match = matching.match_token(ev.canonical)
        if match and match.confidence >= settings().exact_match_confidence:
            return str(match.ingredient_id)
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
