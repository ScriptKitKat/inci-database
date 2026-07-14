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
import uuid
from typing import Any
from urllib.parse import urlsplit

from .. import db, matching
from ..config import settings
from ..evidence import SPELLING_SOURCES, has_spelling_disagreement
from ..llm import batch as llm_batch
from ..llm.prompts import render
from ..models import Evidence, Hypothesis, ProductFinding, TokenJudgment
from ..normalize import normalize_name

logger = logging.getLogger(__name__)

# Five searches cover an official site, major retailer, and ingredient reference
# while keeping the product-level request bounded.
WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}

# Batch statuses that will never make further progress.
_TERMINAL = llm_batch.TERMINAL_STATUSES


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------


def submit(limit: int | None = None) -> dict[str, int]:
    s = settings()
    counters = {
        "submissions": 0,
        "requests": 0,
        "batches": 0,
        "finalized": 0,
        "failed": 0,
        "oversized": 0,
        "stale_recovered": 0,
    }
    counters["stale_recovered"] = db.recover_stale_verification_batches(
        s.stale_claim_minutes
    )
    rows = db.claim_verification_submissions(limit or s.claim_limit)
    prepared: list[tuple[dict[str, Any], list[dict[str, Any]], int]] = []
    for sub in rows:
        try:
            sub_requests = _prepare_submission(sub, counters)
        except Exception as exc:  # noqa: BLE001 - isolate per submission
            logger.exception("verify submit failed for submission %s", sub["id"])
            db.update_submission(
                sub["id"], {"verification_group_id": None, "locked_at": None}
            )
            db.fail_submission(sub["id"], f"{type(exc).__name__}: {exc}")
            counters["failed"] += 1
            continue
        if sub_requests:
            size = len(json.dumps(sub_requests, ensure_ascii=False).encode("utf-8"))
            if len(sub_requests) > s.verification_batch_max_requests or size > s.verification_batch_max_bytes:
                db.update_submission(
                    sub["id"],
                    {
                        "status": "pending_human",
                        "verification_group_id": None,
                        "locked_at": None,
                        "verification": {"verdict": "submission_too_large"},
                    },
                )
                db.audit(sub["id"], "pending_human", {"trigger": "submission_too_large"})
                counters["oversized"] += 1
                continue
            prepared.append((sub, sub_requests, size))

    groups: list[list[tuple[dict[str, Any], list[dict[str, Any]], int]]] = []
    for item in prepared:
        request_count = sum(len(entry[1]) for entry in groups[-1]) if groups else 0
        payload_bytes = sum(entry[2] for entry in groups[-1]) if groups else 0
        if (
            not groups
            or request_count + len(item[1]) > s.verification_batch_max_requests
            or payload_bytes + item[2] > s.verification_batch_max_bytes
        ):
            groups.append([])
        groups[-1].append(item)

    for group in groups:
        group_id = str(uuid.uuid4())
        submission_ids = [item[0]["id"] for item in group]
        requests = [request for item in group for request in item[1]]
        payload_bytes = sum(item[2] for item in group)
        try:
            db.create_verification_batch(
                group_id, submission_ids, len(requests), payload_bytes
            )
        except Exception as exc:  # noqa: BLE001 - no external request was sent
            for submission_id in submission_ids:
                db.update_submission(
                    submission_id,
                    {"verification_group_id": None, "locked_at": None},
                )
                db.fail_submission(submission_id, f"could not record verification batch: {exc}")
            counters["failed"] += len(group)
            continue
        try:
            anthropic_batch_id = llm_batch.submit_batch(requests)
        except Exception as exc:  # noqa: BLE001 - release the rejected send attempt
            db.release_verification_batch(group_id, f"{type(exc).__name__}: {exc}")
            counters["failed"] += len(group)
            continue
        try:
            db.attach_verification_batch(group_id, anthropic_batch_id)
        except Exception as exc:  # noqa: BLE001 - external batch is now unlinked
            db.release_verification_batch(
                group_id, f"batch accepted but attach failed: {exc}", orphaned=True
            )
            counters["failed"] += len(group)
            continue
        counters["batches"] += 1
        counters["submissions"] += len(group)
        counters["requests"] += len(requests)
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

    sync_product = s.sync_product_verification or bool(
        (sub.get("verification") or {}).get("sync_product_verification")
    )
    if sync_product:
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
                    "reason": finding.reason if finding else "Product response could not be parsed.",
                    "resolved_product_name": (
                        finding.matched_product_name if finding else None
                    ),
                    "verdict": "pending" if finding else "error",
                }
            },
        )
        if not unresolved:
            _finalize(
                sub["id"],
                tokens,
                finding,
                submitted_product_name=sub["product_name"],
                submitted_brand_name=sub["brand_name"],
            )
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
    by_id = {row["id"]: row for row in rows}
    for batch in db.fetch_verification_batches("submitted"):
        batch_id = batch["anthropic_batch_id"]
        subs = [by_id[sid] for sid in batch["submission_ids"] if sid in by_id]
        try:
            status = llm_batch.batch_status(batch_id)
        except Exception as exc:  # noqa: BLE001 - missing lookup is a terminal batch failure
            db.release_verification_batch(batch["id"], f"batch lookup failed: {exc}")
            _mark_sync_fallback(subs)
            counters["failed"] += len(subs)
            continue
        if status not in _TERMINAL:
            counters["waiting"] += len(subs)
            continue
        if status != "ended":
            db.release_verification_batch(
                batch["id"], f"anthropic batch {batch_id} {status}"
            )
            _mark_sync_fallback(subs)
            counters["failed"] += len(subs)
            continue
        results = dict(llm_batch.batch_results(batch_id))
        for sub in subs:
            if sub.get("anthropic_batch_id") != batch_id:
                continue
            try:
                _apply_results(sub, results)
                counters["finalized"] += 1
            except Exception as exc:  # noqa: BLE001 - isolate per submission
                logger.exception("verify poll failed for submission %s", sub["id"])
                db.update_submission(sub["id"], {"anthropic_batch_id": None})
                db.fail_submission(sub["id"], f"{type(exc).__name__}: {exc}")
                counters["failed"] += 1
        db.close_verification_batch(batch["id"], "ended")
    return counters


def _mark_sync_fallback(submissions: list[dict[str, Any]]) -> None:
    """After two terminal batch failures, retry product search synchronously.

    The small marker lives in verification so it survives the next worker tick;
    the sync result replaces it immediately.
    """
    for sub in submissions:
        if int(sub.get("attempt_count") or 0) >= 2:
            verification = dict(sub.get("verification") or {})
            verification["sync_product_verification"] = True
            db.update_submission(sub["id"], {"verification": verification})


def _apply_results(sub: dict[str, Any], results: dict[str, str | None]) -> None:
    tokens = db.fetch_tokens(sub["id"])
    escalation_triggers: list[str] = []
    token_updates: list[dict[str, Any]] = []
    product_key = f"product_{sub['id']}"
    if product_key in results:
        finding = parse_product_finding(results[product_key])
    else:
        finding = _finding_from_interim(sub.get("verification") or {})
    published_names = _trusted_formula_canonical_names(sub["id"], tokens, finding)
    for token in tokens:
        if token["resolution"] != "unresolved":
            continue
        published_name = published_names.get(token["id"])
        if published_name:
            fields = {
                "resolution": "new_ingredient",
                "resolution_source": "deterministic",
                "canonical_name": published_name,
                "matched_ingredient_id": None,
                "match_type": None,
                "match_confidence": None,
            }
            trigger = None
        else:
            judgment = parse_token_judgment(results.get(f"token_{token['id']}"))
            fields, trigger = _evaluate_judgment(judgment, build_hypotheses(token), token)
        token.update(fields)
        if trigger:
            escalation_triggers.append(trigger)
        token_updates.append({"token_id": token["id"], "fields": fields, "trigger": trigger})

    _finalize(
        sub["id"],
        tokens,
        finding,
        escalation_triggers,
        expected_batch_id=sub.get("anthropic_batch_id"),
        token_updates=token_updates,
        submitted_product_name=sub["product_name"],
        submitted_brand_name=sub["brand_name"],
    )


def _finalize(
    submission_id: str,
    tokens: list[dict[str, Any]],
    finding: ProductFinding | None,
    escalation_triggers: list[str] | None = None,
    *,
    expected_batch_id: str | None = None,
    token_updates: list[dict[str, Any]] | None = None,
    submitted_product_name: str | None = None,
    submitted_brand_name: str | None = None,
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
            "reason": "Product response could not be parsed.",
            "submitted_coverage": 0.0,
            "online_coverage": 0.0,
            "verdict": "error",
        }
    else:
        trusted = finding.found and is_trusted_product_url(submission_id, finding.source_url)
        submitted_coverage, online_coverage = coverage(
            [t["raw_token"] for t in kept], finding.online_ingredients
        )
        if not finding.found:
            verdict = "not_found"
        elif not trusted:
            verdict = "untrusted_source"
        elif not finding.online_ingredients:
            verdict = "no_list"
        elif (
            submitted_coverage >= s.product_overlap_threshold
            and online_coverage >= s.product_overlap_threshold
        ):
            resolved_name = (finding.matched_product_name or "").strip()
            name_changed = bool(
                resolved_name
                and submitted_product_name
                and _should_resolve_product_name(
                    submitted_product_name, resolved_name, submitted_brand_name
                )
            )
            verdict = "name_resolved" if name_changed else "verified"
        else:
            verdict = "divergent"
        verification = {
            "found": finding.found,
            "source_name": finding.source_name,
            "source_url": finding.source_url,
            "reason": finding.reason,
            "submitted_coverage": round(submitted_coverage, 4),
            "online_coverage": round(online_coverage, 4),
            "verdict": verdict,
        }
        if finding.matched_product_name:
            verification["resolved_product_name"] = finding.matched_product_name
        if verdict == "name_resolved":
            verification["submitted_product_name"] = submitted_product_name
        if verdict in ("divergent", "untrusted_source"):
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
    if not db.finalize_submission_verification(
        submission_id,
        expected_batch_id,
        token_updates or [],
        verification,
        status,
        trigger,
    ):
        raise RuntimeError("stale verification batch result")


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
    # Backstop for tokens that predate intake-time escalation.
    return has_spelling_disagreement(token.get("evidence") or [])


def _submission_trigger(
    verdict: str, pending_tokens: bool, all_junk: bool, token_triggers: list[str]
) -> str:
    if all_junk:
        return "all_tokens_junk"
    if token_triggers:
        return token_triggers[0]
    if verdict == "name_resolved":
        return "product_name_resolved"
    if pending_tokens:
        return "unresolved_tokens"
    return {
        "not_found": "product_not_found",
        "no_list": "product_ingredient_list_missing",
        "untrusted_source": "product_source_untrusted",
        "name_resolved": "product_name_resolved",
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
    if not isinstance(data, dict) or type(data.get("found")) is not bool:
        return None
    reason = data.get("reason")
    if not isinstance(reason, str):
        return None
    if not data["found"]:
        return ProductFinding(found=False, reason=reason)
    source_name = data.get("source_name")
    source_url = data.get("source_url")
    matched_product_name = data.get("matched_product_name")
    online = data.get("online_ingredients")
    if not isinstance(source_name, str) or not source_name.strip():
        return None
    if not _valid_https_url(source_url):
        return None
    if not isinstance(online, list) or any(not isinstance(t, str) or not t.strip() for t in online):
        return None
    return ProductFinding(
        found=True,
        source_name=source_name.strip(),
        source_url=source_url,
        online_ingredients=[t.strip() for t in online],
        reason=reason,
        matched_product_name=(
            matched_product_name.strip()
            if isinstance(matched_product_name, str) and matched_product_name.strip()
            else None
        ),
    )


def _finding_from_interim(verification: dict[str, Any]) -> ProductFinding | None:
    if verification.get("verdict") == "error" or "found" not in verification:
        return None
    return ProductFinding(
        found=bool(verification.get("found")),
        source_name=verification.get("source_name"),
        source_url=verification.get("source_url"),
        online_ingredients=list(verification.get("online_tokens") or []),
        reason=str(verification.get("reason") or ""),
        matched_product_name=verification.get("resolved_product_name"),
    )


def _valid_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
    )


def _hostname(value: str | None) -> str | None:
    if not _valid_https_url(value):
        return None
    host = (urlsplit(value or "").hostname or "").lower().rstrip(".")
    return host.removeprefix("www.") or None


def _domain_matches(host: str, domain: str) -> bool:
    domain = domain.strip().lower().rstrip(".").removeprefix("www.")
    return bool(domain) and (host == domain or host.endswith(f".{domain}"))


def is_trusted_product_url(submission_id: str, source_url: str | None) -> bool:
    host = _hostname(source_url)
    if not host:
        return False
    configured = settings().trusted_product_domains.split(",")
    registered = db.fetch_brand_product_domains(submission_id)
    return any(_domain_matches(host, domain) for domain in [*configured, *registered])


def normalize_for_overlap(entry: str) -> set[str]:
    """Return the explicit alternative spellings represented by one entry."""
    raw_alternatives = [entry]
    raw_alternatives.extend(re.findall(r"\(([^)]*)\)", entry))
    raw_alternatives.append(re.sub(r"\([^)]*\)", " ", entry))
    values: set[str] = set()
    for alternative in raw_alternatives:
        for part in alternative.split("/"):
            normalized = normalize_name(part)
            if normalized in {"aqua", "water", "eau"}:
                normalized = "water"
            if normalized:
                values.add(normalized)
    return values


def _should_resolve_product_name(
    submitted: str, published: str, brand_name: str | None = None
) -> bool:
    """Escalate a real rename, but preserve an already-more-specific title."""
    submitted_name = normalize_name(re.sub(r"[™®©]", "", submitted))
    published_name = normalize_name(re.sub(r"[™®©]", "", published))
    normalized_brand = normalize_name(brand_name or "")
    if normalized_brand and published_name.startswith(f"{normalized_brand} "):
        published_name = published_name[len(normalized_brand) :].strip()
    if not submitted_name or not published_name or submitted_name == published_name:
        return False
    return not set(published_name.split()).issubset(submitted_name.split())


def _trusted_formula_canonical_names(
    submission_id: str,
    tokens: list[dict[str, Any]],
    finding: ProductFinding | None,
) -> dict[str, str]:
    """Use a fully matching trusted product list as deterministic spelling evidence."""
    if (
        finding is None
        or not finding.found
        or not finding.online_ingredients
        or not is_trusted_product_url(submission_id, finding.source_url)
    ):
        return {}
    kept = [token for token in tokens if token["resolution"] != "junk"]
    submitted_coverage, online_coverage = coverage(
        [token["raw_token"] for token in kept], finding.online_ingredients
    )
    threshold = settings().product_overlap_threshold
    if submitted_coverage < threshold or online_coverage < threshold:
        return {}

    online = [normalize_for_overlap(name) for name in finding.online_ingredients]
    used: set[int] = set()
    names: dict[str, str] = {}
    for token in kept:
        if token["resolution"] != "unresolved":
            continue
        alternatives = normalize_for_overlap(token["raw_token"])
        matches = [
            index
            for index, candidate in enumerate(online)
            if index not in used and alternatives & candidate
        ]
        if len(matches) == 1:
            index = matches[0]
            used.add(index)
            names[token["id"]] = finding.online_ingredients[index].strip()
    return names


def coverage(submitted: list[str], online: list[str]) -> tuple[float, float]:
    if not submitted or not online:
        return 0.0, 0.0
    left = [normalize_for_overlap(value) for value in submitted]
    right = [normalize_for_overlap(value) for value in online]
    used: set[int] = set()
    matches = 0
    for alternatives in left:
        match = next(
            (
                index
                for index, candidate in enumerate(right)
                if index not in used and alternatives & candidate
            ),
            None,
        )
        if match is not None:
            used.add(match)
            matches += 1
    return matches / len(left), matches / len(right)


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
