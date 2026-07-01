from __future__ import annotations

import json
from uuid import UUID

from pydantic import ValidationError

from .models import CurationDecision, IngredientEdge, IngredientEvidence
from .scoring import NameScore, is_spelling_merge_candidate

AUTO_APPLY_CONFIDENCE = 0.90
LLM_MIN_CONFIDENCE = 0.80


def source_verified(evidence: list[IngredientEvidence]) -> bool:
    return any(ev.found and ev.lookup_type in {"exact", "page"} for ev in evidence)


def choose_deterministic_decision(
    *,
    source_ingredient_id: UUID,
    normalized_name: str,
    canonical_collisions: list[dict],
    alias_collisions: list[dict],
    source_evidence: list[IngredientEvidence],
    spelling_scores: list[NameScore],
) -> tuple[CurationDecision, IngredientEdge | None, str]:
    if canonical_collisions:
        target = _oldest(canonical_collisions)
        return (
            CurationDecision(
                decision="merge_into_existing",
                target_ingredient_id=UUID(target["id"]),
                canonical_inci_name=target.get("inci_name"),
                aliases_to_add=[],
                confidence=0.99,
                reason="normalized name exactly matches an existing canonical ingredient",
            ),
            IngredientEdge(
                source_ingredient_id=source_ingredient_id,
                target_ingredient_id=UUID(target["id"]),
                source_normalized_name=normalized_name,
                target_normalized_name=target["normalized_name"],
                relationship_type="canonical_exact",
                pg_trgm_similarity=1.0,
                edit_distance=0,
                token_overlap=1.0,
                score_margin=1.0,
            ),
            "deterministic",
        )

    unique_alias_targets = _unique_by_id(alias_collisions, "ingredient_id")
    if len(unique_alias_targets) == 1:
        target = unique_alias_targets[0]
        return (
            CurationDecision(
                decision="alias_to_existing",
                target_ingredient_id=UUID(target["ingredient_id"]),
                canonical_inci_name=target.get("inci_name"),
                aliases_to_add=[],
                confidence=0.97,
                reason="normalized name exactly matches an existing ingredient alias",
            ),
            IngredientEdge(
                source_ingredient_id=source_ingredient_id,
                target_ingredient_id=UUID(target["ingredient_id"]),
                source_normalized_name=normalized_name,
                target_normalized_name=target.get("normalized_name") or normalized_name,
                relationship_type="alias_exact",
                pg_trgm_similarity=0.98,
                edit_distance=0,
                token_overlap=1.0,
                score_margin=1.0,
            ),
            "deterministic",
        )
    if len(unique_alias_targets) > 1:
        return (
            CurationDecision(
                decision="needs_human",
                confidence=0.0,
                reason="normalized name matches aliases for multiple existing ingredients",
            ),
            None,
            "deterministic",
        )

    if spelling_scores:
        best = spelling_scores[0]
        if is_spelling_merge_candidate(normalized_name, best):
            return (
                CurationDecision(
                    decision="merge_into_existing",
                    target_ingredient_id=UUID(best.target_ingredient_id),
                    aliases_to_add=[],
                    confidence=min(0.96, max(0.90, best.similarity)),
                    reason="normalized name is a high-confidence spelling correction of a source-verified ingredient",
                ),
                IngredientEdge(
                    source_ingredient_id=source_ingredient_id,
                    target_ingredient_id=UUID(best.target_ingredient_id),
                    source_normalized_name=normalized_name,
                    target_normalized_name=best.target_normalized_name,
                    relationship_type="spelling_candidate",
                    pg_trgm_similarity=best.similarity,
                    edit_distance=best.edit_distance,
                    token_overlap=best.token_overlap,
                    score_margin=best.score_margin,
                ),
                "deterministic",
            )

    if source_verified(source_evidence):
        best_source = next(ev for ev in source_evidence if ev.found)
        return (
            CurationDecision(
                decision="keep",
                canonical_inci_name=best_source.canonical_name,
                confidence=max(0.90, best_source.confidence),
                reason=f"verified by {best_source.source}",
            ),
            None,
            "deterministic",
        )

    return (
        CurationDecision(
            decision="needs_human",
            confidence=0.0,
            reason="no deterministic source verification or safe merge target found",
        ),
        None,
        "deterministic",
    )


def parse_llm_decision(raw: str, valid_target_ids: set[UUID]) -> CurationDecision:
    try:
        payload = json.loads(_extract_json(raw))
        decision = CurationDecision(**payload)
    except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as exc:
        return CurationDecision(
            decision="needs_human",
            confidence=0.0,
            reason=f"malformed LLM decision: {type(exc).__name__}",
        )

    if decision.target_ingredient_id and decision.target_ingredient_id not in valid_target_ids:
        return CurationDecision(
            decision="needs_human",
            confidence=0.0,
            reason="LLM referenced an unknown target ingredient id",
        )
    if decision.confidence < LLM_MIN_CONFIDENCE:
        return CurationDecision(
            decision="needs_human",
            confidence=decision.confidence,
            reason=f"LLM confidence below {LLM_MIN_CONFIDENCE}: {decision.reason}",
        )
    return decision


def review_status_for(decision: CurationDecision) -> str:
    if decision.decision == "needs_human":
        return "pending_human"
    if decision.confidence >= AUTO_APPLY_CONFIDENCE:
        return "not_required"
    return "pending_human"


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _oldest(rows: list[dict]) -> dict:
    return sorted(rows, key=lambda row: (row.get("created_at") or "", row.get("id") or ""))[0]


def _unique_by_id(rows: list[dict], id_key: str) -> list[dict]:
    out: dict[str, dict] = {}
    for row in rows:
        if row.get(id_key):
            out.setdefault(row[id_key], row)
    return list(out.values())
