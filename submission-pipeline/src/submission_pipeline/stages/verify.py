"""Verify stage: product web-search verification + per-token LLM judgment.

The LLM never supplies a spelling. Token requests carry hypotheses whose
canonical strings are anchored to the catalog or an authoritative source;
the model may only pick a hypothesis id, or answer junk/unknown. Anything
that fails these rails lands `pending_human`.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from typing import Any

from .. import db, matching
from ..config import settings
from ..evidence import SPELLING_SOURCES
from ..llm import batch as llm_batch
from ..llm.prompts import render
from ..models import Evidence, Hypothesis, ProductFinding, TokenJudgment
from ..normalize import normalize_name

logger = logging.getLogger(__name__)

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}

# Batch statuses that will never make further progress.
_TERMINAL = llm_batch.TERMINAL_STATUSES


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------


def submit(limit: int | None = None) -> dict[str, int]:
    s = settings()
    counters = {"submissions": 0, "requests": 0, "finalized": 0, "failed": 0, "lost_race": 0}
    rows = db.fetch_submissions("verifying", batch_id_is_null=True, limit=limit or s.claim_limit)
    requests: list[dict[str, Any]] = []
    batched_ids: list[str] = []
    for sub in rows:
        try:
            sub_requests = _prepare_submission(sub, counters)
        except Exception as exc:  # noqa: BLE001 - isolate per submission
            logger.exception("verify submit failed for submission %s", sub["id"])
            db.fail_submission(sub["id"], f"{type(exc).__name__}: {exc}")
            counters["failed"] += 1
            continue
        if sub_requests:
            requests.extend(sub_requests)
            batched_ids.append(sub["id"])
            counters["submissions"] += 1

    if requests:
        batch_id = llm_batch.submit_batch(requests)
        counters["requests"] = len(requests)
        for submission_id in batched_ids:
            # Conditional write: an overlapping worker tick may have batched
            # this submission already. Losing the race orphans our batch's
            # requests for it (cost only); poll follows the stored batch id.
            if not db.assign_batch_id(submission_id, batch_id):
                logger.warning(
                    "submission %s already batched by another worker", submission_id
                )
                counters["lost_race"] += 1
    return counters


def _prepare_submission(sub: dict[str, Any], counters: dict[str, int]) -> list[dict[str, Any]]:
    s = settings()
    tokens = db.fetch_tokens(sub["id"])
    unresolved = [t for t in tokens if t["resolution"] == "unresolved"]
    requests: list[dict[str, Any]] = []

    # Two INCI-native sources returning materially different spellings is a
    # disagreement to review, not a vote for the higher-confidence source.
    for token in unresolved:
        if _has_spelling_disagreement(token):
            fields = {"resolution": "pending_human"}
            db.update_token(token["id"], fields)
            token.update(fields)
            db.audit(
                sub["id"],
                "token_escalated",
                {"token_id": token["id"], "trigger": "source_disagreement"},
            )
    unresolved = [t for t in tokens if t["resolution"] == "unresolved"]

    if s.sync_product_verification:
        text = llm_batch.sync_message(_product_params(sub))
        finding = parse_product_finding(text)
        # Interim stash; _finalize recomputes the verdict and strips
        # online_tokens unless the list is divergent.
        db.update_submission(
            sub["id"],
            {
                "verification": {
                    "found": finding.found if finding else False,
                    "source_name": finding.source_name if finding else None,
                    "source_url": finding.source_url if finding else None,
                    "online_tokens": finding.online_ingredients if finding else [],
                    "verdict": "pending" if finding else "error",
                }
            },
        )
        if not unresolved:
            _finalize(sub["id"], tokens, finding)
            counters["finalized"] += 1
            return []
    else:
        requests.append({"custom_id": f"product_{sub['id']}", "params": _product_params(sub)})

    for token in unresolved:
        requests.append(
            {
                "custom_id": f"token_{token['id']}",
                "params": _token_params(sub, token, build_hypotheses(token)),
            }
        )
    return requests


def _product_params(sub: dict[str, Any]) -> dict[str, Any]:
    s = settings()
    return {
        "model": s.judge_model,
        "max_tokens": s.judge_max_tokens,
        "temperature": s.judge_temperature,
        "tools": [WEB_SEARCH_TOOL],
        "messages": [
            {
                "role": "user",
                "content": render(
                    "verify_product",
                    brand_name=sub["brand_name"],
                    product_name=sub["product_name"],
                ),
            }
        ],
    }


def _token_params(
    sub: dict[str, Any], token: dict[str, Any], hypotheses: list[Hypothesis]
) -> dict[str, Any]:
    s = settings()
    rendered_hypotheses = (
        json.dumps([h.to_json() for h in hypotheses], ensure_ascii=False, indent=2)
        if hypotheses
        else "(none — no anchored spelling exists for this token)"
    )
    return {
        "model": s.judge_model,
        "max_tokens": s.judge_max_tokens,
        "temperature": s.judge_temperature,
        "messages": [
            {
                "role": "user",
                "content": render(
                    "verify_token",
                    brand_name=sub["brand_name"],
                    product_name=sub["product_name"],
                    raw_token=token["raw_token"],
                    normalized_token=token["normalized_token"],
                    hypotheses=rendered_hypotheses,
                ),
            }
        ],
    }


def build_hypotheses(token: dict[str, Any]) -> list[Hypothesis]:
    """Rebuilt deterministically from the token row, so submit and poll
    produce identical ids without persisting anything extra."""
    s = settings()
    hypotheses: list[Hypothesis] = []

    confidence = token.get("match_confidence")
    if (
        token.get("matched_ingredient_id")
        and confidence is not None
        and s.fuzzy_hypothesis_threshold <= float(confidence) < s.exact_match_confidence
    ):
        ingredient = db.fetch_ingredient(token["matched_ingredient_id"])
        if ingredient:
            hypotheses.append(
                Hypothesis(
                    id="fuzzy",
                    kind="existing",
                    canonical=ingredient["inci_name"],
                    source=f"catalog:{token.get('match_type')}",
                    confidence=float(confidence),
                    ingredient_id=token["matched_ingredient_id"],
                )
            )

    evidence_rows = list(enumerate(token.get("evidence") or []))
    evidence_rows.sort(key=lambda row: float((row[1] or {}).get("confidence") or 0.0), reverse=True)
    for index, raw in evidence_rows:
        ev = Evidence.from_json(raw)
        # PubChem corroboration is retained for review, but the plan explicitly
        # excludes it from the token prompt—even when its name maps to a row.
        if not ev.found or not ev.canonical or ev.source not in SPELLING_SOURCES:
            continue
        match = matching.match_token(ev.canonical)
        if match and match.confidence >= s.exact_match_confidence:
            hypotheses.append(
                Hypothesis(
                    id=f"evidence_{index}",
                    kind="existing",
                    canonical=ev.canonical,
                    source=ev.source,
                    confidence=ev.confidence,
                    ingredient_id=str(match.ingredient_id),
                )
            )
        else:
            hypotheses.append(
                Hypothesis(
                    id=f"evidence_{index}",
                    kind="authoritative",
                    canonical=ev.canonical,
                    source=ev.source,
                    confidence=ev.confidence,
                )
            )
    return hypotheses


# ---------------------------------------------------------------------------
# Poll
# ---------------------------------------------------------------------------


def poll() -> dict[str, int]:
    counters = {"finalized": 0, "waiting": 0, "failed": 0}
    rows = db.fetch_submissions("verifying", batch_id_is_null=False)
    by_batch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_batch[row["anthropic_batch_id"]].append(row)

    for batch_id, subs in by_batch.items():
        status = llm_batch.batch_status(batch_id)
        if status not in _TERMINAL:
            counters["waiting"] += len(subs)
            continue
        if status != "ended":
            for sub in subs:
                db.update_submission(sub["id"], {"anthropic_batch_id": None})
                db.fail_submission(sub["id"], f"anthropic batch {batch_id} {status}")
                counters["failed"] += 1
            continue
        results = dict(llm_batch.batch_results(batch_id))
        for sub in subs:
            try:
                _apply_results(sub, results)
                counters["finalized"] += 1
            except Exception as exc:  # noqa: BLE001 - isolate per submission
                logger.exception("verify poll failed for submission %s", sub["id"])
                db.update_submission(sub["id"], {"anthropic_batch_id": None})
                db.fail_submission(sub["id"], f"{type(exc).__name__}: {exc}")
                counters["failed"] += 1
    return counters


def _apply_results(sub: dict[str, Any], results: dict[str, str | None]) -> None:
    tokens = db.fetch_tokens(sub["id"])
    escalation_triggers: list[str] = []
    for token in tokens:
        if token["resolution"] != "unresolved":
            continue
        judgment = parse_token_judgment(results.get(f"token_{token['id']}"))
        fields, trigger = _evaluate_judgment(judgment, build_hypotheses(token), token)
        db.update_token(token["id"], fields)
        token.update(fields)
        if trigger:
            escalation_triggers.append(trigger)
            db.audit(
                sub["id"],
                "token_escalated",
                {"token_id": token["id"], "trigger": trigger},
            )

    product_key = f"product_{sub['id']}"
    if product_key in results:
        finding = parse_product_finding(results[product_key])
    else:
        finding = _finding_from_interim(sub.get("verification") or {})
    _finalize(sub["id"], tokens, finding, escalation_triggers)


def _finalize(
    submission_id: str,
    tokens: list[dict[str, Any]],
    finding: ProductFinding | None,
    escalation_triggers: list[str] | None = None,
) -> None:
    s = settings()
    kept = [t for t in tokens if t["resolution"] != "junk"]
    pending = any(t["resolution"] in ("pending_human", "unresolved") for t in tokens)
    all_junk = bool(tokens) and not kept

    if finding is None:
        verification: dict[str, Any] = {
            "found": False,
            "source_name": None,
            "source_url": None,
            "overlap": 0.0,
            "verdict": "error",
        }
    else:
        overlap = (
            token_overlap([t["raw_token"] for t in kept], finding.online_ingredients)
            if finding.found
            else 0.0
        )
        if not finding.found:
            verdict = "not_found"
        elif not finding.online_ingredients:
            verdict = "no_list"
        elif overlap >= s.product_overlap_threshold:
            verdict = "verified"
        else:
            verdict = "divergent"
        verification = {
            "found": finding.found,
            "source_name": finding.source_name,
            "source_url": finding.source_url,
            "overlap": round(overlap, 4),
            "verdict": verdict,
        }
        if verdict == "divergent":
            # Kept only for the review diff; apply strips it again.
            verification["online_tokens"] = finding.online_ingredients

    status = (
        "decision_ready"
        if verification["verdict"] == "verified" and not pending and not all_junk
        else "pending_human"
    )
    trigger = None
    if status == "pending_human":
        trigger = _submission_trigger(
            verification["verdict"], pending, all_junk, escalation_triggers or []
        )
    db.update_submission(
        submission_id,
        {
            "status": status,
            "verification": verification,
            "anthropic_batch_id": None,
            "locked_at": None,
        },
    )
    db.audit(
        submission_id,
        "verified",
        {
            "verdict": verification["verdict"],
            "status": status,
            "overlap": verification["overlap"],
            **({"trigger": trigger} if trigger else {}),
        },
    )


def _judgment_fields(
    judgment: TokenJudgment,
    hypotheses: list[Hypothesis],
    token: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decision policy. Every rail failure falls through to pending_human."""
    fields, _ = _evaluate_judgment(judgment, hypotheses, token or {})
    return fields


def _evaluate_judgment(
    judgment: TokenJudgment, hypotheses: list[Hypothesis], token: dict[str, Any]
) -> tuple[dict[str, Any], str | None]:
    s = settings()
    by_id = {h.id: h for h in hypotheses}
    choice = by_id.get(judgment.choice_id) if judgment.choice_id else None

    if (
        judgment.verdict == "junk"
        and judgment.choice_id is None
        and judgment.confidence >= s.junk_confidence_threshold
    ):
        position = int(token.get("position") or 0)
        if 1 <= position <= 3:
            return {"resolution": "pending_human"}, "junk_at_top_positions"
        return {"resolution": "junk", "resolution_source": "llm"}, None

    if judgment.verdict == "matched" and choice and choice.kind == "existing":
        if judgment.confidence >= s.match_confirm_threshold:
            return _matched_fields(choice), None

    if judgment.verdict == "new_ingredient" and choice:
        if choice.kind == "existing":
            if (
                choice.id.startswith("evidence_")
                and judgment.confidence >= s.match_confirm_threshold
            ):
                # The catalog caught up between submit and poll; matching to
                # the row now anchoring this source spelling is equivalent.
                return _matched_fields(choice), None
        elif judgment.confidence >= s.new_ingredient_confirm_threshold:
            return (
                {
                    "resolution": "new_ingredient",
                    "resolution_source": "llm",
                    "canonical_name": choice.canonical,
                    "matched_ingredient_id": None,
                    "match_type": None,
                    "match_confidence": None,
                },
                None,
            )

    return {"resolution": "pending_human"}, _judgment_trigger(judgment, by_id, choice)


def _judgment_trigger(
    judgment: TokenJudgment,
    by_id: dict[str, Hypothesis],
    choice: Hypothesis | None,
) -> str:
    if judgment.reason == "no parseable result" or judgment.reason.startswith("invalid "):
        return "llm_response_invalid"
    if judgment.verdict == "unknown":
        return "llm_unknown"
    if judgment.verdict in ("matched", "new_ingredient") and choice is None:
        return "llm_choice_id_invalid"
    if judgment.verdict == "junk" and judgment.choice_id is not None:
        return "llm_choice_id_invalid"
    if judgment.verdict == "matched" and choice and choice.kind != "existing":
        return "matched_non_catalog_hypothesis"
    if (
        judgment.verdict == "new_ingredient"
        and choice
        and choice.kind == "existing"
        and not choice.id.startswith("evidence_")
    ):
        return "llm_verdict_choice_mismatch"
    return "llm_confidence_below_threshold"


def _has_spelling_disagreement(token: dict[str, Any]) -> bool:
    spellings = {
        normalize_name(str(raw.get("canonical") or ""))
        for raw in token.get("evidence") or []
        if raw.get("found") and raw.get("source") in SPELLING_SOURCES and raw.get("canonical")
    }
    return len(spellings) > 1


def _submission_trigger(
    verdict: str, pending_tokens: bool, all_junk: bool, token_triggers: list[str]
) -> str:
    if all_junk:
        return "all_tokens_junk"
    if token_triggers:
        return token_triggers[0]
    if pending_tokens:
        return "unresolved_tokens"
    return {
        "not_found": "product_not_found",
        "no_list": "product_ingredient_list_missing",
        "divergent": "divergent_list",
        "error": "product_result_invalid",
    }.get(verdict, "verification_incomplete")


def _matched_fields(choice: Hypothesis) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "resolution": "matched",
        "resolution_source": "llm",
        "matched_ingredient_id": choice.ingredient_id,
    }
    if choice.id != "fuzzy":
        # Cross-source synonym, not a catalog fuzzy hit: the intake match
        # metadata refers to a different candidate, so drop it (apply then
        # records the raw token as a 'synonym' alias, not a 'typo').
        fields["match_type"] = None
        fields["match_confidence"] = None
    return fields


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_token_judgment(text: str | None) -> TokenJudgment:
    data = _extract_json(text)
    required = {"verdict", "choice_id", "confidence", "reason"}
    if not isinstance(data, dict) or not required.issubset(data):
        return TokenJudgment("unknown", None, 0.0, "no parseable result")
    verdict = data.get("verdict")
    if verdict not in ("matched", "new_ingredient", "junk", "unknown"):
        return TokenJudgment("unknown", None, 0.0, "invalid verdict")
    choice_id = data.get("choice_id")
    if choice_id is not None and not isinstance(choice_id, str):
        return TokenJudgment("unknown", None, 0.0, "invalid choice_id")
    if not isinstance(data.get("reason"), str):
        return TokenJudgment("unknown", None, 0.0, "invalid reason")
    raw_confidence = data.get("confidence")
    if isinstance(raw_confidence, bool) or not isinstance(raw_confidence, (int, float)):
        return TokenJudgment("unknown", None, 0.0, "invalid confidence")
    confidence = float(raw_confidence)
    if not 0.0 <= confidence <= 1.0:
        return TokenJudgment("unknown", None, 0.0, "invalid confidence")
    return TokenJudgment(
        verdict=verdict,
        choice_id=choice_id or None,
        confidence=confidence,
        reason=str(data.get("reason") or ""),
    )


def parse_product_finding(text: str | None) -> ProductFinding | None:
    data = _extract_json(text)
    if not isinstance(data, dict) or "found" not in data:
        return None
    online = data.get("online_ingredients")
    return ProductFinding(
        found=bool(data.get("found")),
        source_name=data.get("source_name") or None,
        source_url=data.get("source_url") or None,
        online_ingredients=[str(t) for t in online if str(t).strip()]
        if isinstance(online, list)
        else [],
    )


def _finding_from_interim(verification: dict[str, Any]) -> ProductFinding | None:
    if verification.get("verdict") == "error" or "found" not in verification:
        return None
    return ProductFinding(
        found=bool(verification.get("found")),
        source_name=verification.get("source_name"),
        source_url=verification.get("source_url"),
        online_ingredients=list(verification.get("online_tokens") or []),
    )


def token_overlap(submitted: list[str], online: list[str]) -> float:
    a = {normalize_name(t) for t in submitted} - {""}
    b = {normalize_name(t) for t in online} - {""}
    if not a:
        return 0.0
    return len(a & b) / len(a)


def _extract_json(text: str | None) -> Any:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
