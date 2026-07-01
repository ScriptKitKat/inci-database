from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any
from uuid import UUID

from ..config import settings
from ..curation.decisions import choose_deterministic_decision, review_status_for
from ..curation.models import CurationDecision, IngredientEvidence, NoopReviewSink
from ..curation.scoring import NameScore, edit_distance, token_overlap, trigram_similarity
from ..db import client
from ..sources.ingredient_verification import (
    OBFIngredientLookup,
    PubChemNameLookup,
    WikidataNameLookup,
    incidecoder_lookup,
    specialchem_lookup,
)

log = logging.getLogger(__name__)


def queue_window(since: datetime, until: datetime) -> int:
    res = (
        client()
        .rpc(
            "enqueue_ingredient_name_curation_window",
            {"p_since": since.isoformat(), "p_until": until.isoformat()},
        )
        .execute()
    )
    return int(res.data or 0)


def run(limit: int = 500) -> str:
    run_id = _create_run("deterministic", {"limit": limit})
    rows = _claim_queue(limit)
    decided = 0
    try:
        existing_rows = _fetch_existing_ingredients()
        source_verified_ids = _fetch_source_verified_ingredient_ids()
        source_verified_rows = [
            row for row in existing_rows if UUID(row["id"]) in source_verified_ids
        ]
        source_clients = _source_clients()
        pending_human: list[UUID] = []

        for row in rows:
            try:
                decision_id = _process_candidate(
                    run_id=run_id,
                    row=row,
                    existing_rows=existing_rows,
                    source_verified_rows=source_verified_rows,
                    source_clients=source_clients,
                )
                if decision_id:
                    decided += 1
                    pending_human.append(decision_id)
            except Exception as exc:
                log.warning("curation failed for queue row %s: %s", row["queue_id"], exc)
                _fail_queue(UUID(row["queue_id"]), exc)

        NoopReviewSink().send(pending_human)
        _finish_run(run_id, "success", rows_in=len(rows), rows_decided=decided)
        return run_id
    except Exception as exc:
        _finish_run(run_id, "failed", rows_in=len(rows), rows_decided=decided, error=exc)
        raise


def apply(run_id: UUID) -> list[str]:
    decisions = (
        client()
        .table("ingredient_curation_decisions")
        .select("id")
        .eq("run_id", str(run_id))
        .in_("review_status", ["not_required", "approved"])
        .in_("decision", ["keep", "merge_into_existing", "alias_to_existing"])
        .execute()
    )
    messages: list[str] = []
    for row in decisions.data or []:
        res = (
            client()
            .rpc("apply_ingredient_curation_decision", {"p_decision_id": row["id"]})
            .execute()
        )
        messages.append(str(res.data))
    return messages


def _process_candidate(
    *,
    run_id: str,
    row: dict[str, Any],
    existing_rows: list[dict[str, Any]],
    source_verified_rows: list[dict[str, Any]],
    source_clients: list[Any],
) -> UUID | None:
    source_id = UUID(row["ingredient_id"])
    normalized_name = row["normalized_name"]
    candidate_id = _insert_candidate(run_id, row)

    canonical_collisions = [
        existing
        for existing in existing_rows
        if existing["id"] != str(source_id)
        and existing.get("normalized_name") == normalized_name
    ]
    alias_collisions = _fetch_alias_collisions(normalized_name)

    evidence = _db_evidence(canonical_collisions, alias_collisions)
    evidence.extend(_lookup_sources(source_clients, normalized_name))
    _insert_evidence(run_id, candidate_id, evidence)

    spelling_scores = _score_spelling_candidates(
        source_id=source_id,
        normalized_name=normalized_name,
        rows=source_verified_rows,
    )

    decision, edge, decision_source = choose_deterministic_decision(
        source_ingredient_id=source_id,
        normalized_name=normalized_name,
        canonical_collisions=canonical_collisions,
        alias_collisions=alias_collisions,
        source_evidence=evidence,
        spelling_scores=spelling_scores,
    )
    edge_id = None
    if edge:
        edge_id = _insert_edge(run_id, candidate_id, edge.model_dump(mode="json"))
    for score in spelling_scores[:5]:
        if edge and str(edge.target_ingredient_id) == score.target_ingredient_id:
            continue
        _insert_edge(
            run_id,
            candidate_id,
            {
                "source_ingredient_id": str(source_id),
                "target_ingredient_id": score.target_ingredient_id,
                "source_normalized_name": normalized_name,
                "target_normalized_name": score.target_normalized_name,
                "relationship_type": "spelling_neighbor",
                "pg_trgm_similarity": score.similarity,
                "edit_distance": score.edit_distance,
                "token_overlap": score.token_overlap,
                "score_margin": score.score_margin,
            },
        )
    decision_id = _insert_decision(
        run_id=run_id,
        queue_id=UUID(row["queue_id"]),
        candidate_id=candidate_id,
        source_ingredient_id=source_id,
        decision=decision,
        decision_source=decision_source,
    )
    _mark_queue_after_decision(UUID(row["queue_id"]), decision)
    log.info(
        "curated %s -> %s (%s)",
        row["inci_name"],
        decision.decision,
        edge_id or "no-edge",
    )
    return decision_id


def _source_clients() -> list[Any]:
    s = settings()
    clients: list[Any] = [OBFIngredientLookup(s.obf_taxonomy_path)]
    clients.extend(
        [
            PubChemNameLookup(),
            WikidataNameLookup(),
            specialchem_lookup(),
            incidecoder_lookup(),
        ]
    )
    return clients


def _lookup_sources(clients: Iterable[Any], normalized_name: str) -> list[IngredientEvidence]:
    evidence: list[IngredientEvidence] = []
    for source_client in clients:
        try:
            evidence.extend(source_client.lookup(normalized_name))
        except Exception as exc:
            evidence.append(
                IngredientEvidence(
                    source=source_client.__class__.__name__,
                    lookup_type="error",
                    found=False,
                    raw_payload={"error": f"{type(exc).__name__}: {exc}"[:500]},
                )
            )
    return evidence


def _db_evidence(
    canonical_collisions: list[dict[str, Any]],
    alias_collisions: list[dict[str, Any]],
) -> list[IngredientEvidence]:
    evidence: list[IngredientEvidence] = []
    for row in canonical_collisions:
        evidence.append(
            IngredientEvidence(
                source="database",
                lookup_type="exact",
                found=True,
                canonical_name=row.get("inci_name"),
                normalized_canonical=row.get("normalized_name"),
                confidence=1.0,
                raw_payload={"ingredient_id": row.get("id")},
            )
        )
    for row in alias_collisions:
        evidence.append(
            IngredientEvidence(
                source="database",
                lookup_type="alias",
                found=True,
                canonical_name=row.get("inci_name"),
                normalized_canonical=row.get("normalized_name"),
                confidence=0.98,
                raw_payload={
                    "ingredient_id": row.get("ingredient_id"),
                    "alias": row.get("alias"),
                },
            )
        )
    return evidence


def _score_spelling_candidates(
    *,
    source_id: UUID,
    normalized_name: str,
    rows: list[dict[str, Any]],
) -> list[NameScore]:
    scores: list[NameScore] = []
    for row in rows:
        if row["id"] == str(source_id):
            continue
        target = row.get("normalized_name") or ""
        if not target or target == normalized_name:
            continue
        sim = trigram_similarity(normalized_name, target)
        if sim < 0.72:
            continue
        scores.append(
            NameScore(
                target_ingredient_id=row["id"],
                target_normalized_name=target,
                similarity=sim,
                edit_distance=edit_distance(normalized_name, target),
                token_overlap=token_overlap(normalized_name, target),
            )
        )
    scores.sort(key=lambda score: (score.similarity, -score.edit_distance), reverse=True)
    if scores:
        second = scores[1].similarity if len(scores) > 1 else 0
        scores[0] = NameScore(
            target_ingredient_id=scores[0].target_ingredient_id,
            target_normalized_name=scores[0].target_normalized_name,
            similarity=scores[0].similarity,
            edit_distance=scores[0].edit_distance,
            token_overlap=scores[0].token_overlap,
            score_margin=scores[0].similarity - second,
        )
    return scores


def _claim_queue(limit: int) -> list[dict[str, Any]]:
    res = (
        client()
        .rpc("claim_ingredient_name_curation_queue", {"p_limit": limit})
        .execute()
    )
    return res.data or []


def _fail_queue(queue_id: UUID, exc: Exception) -> None:
    client().rpc(
        "fail_ingredient_name_curation_queue",
        {"p_queue_id": str(queue_id), "p_error": f"{type(exc).__name__}: {exc}"},
    ).execute()


def _create_run(run_type: str, config: dict[str, Any]) -> str:
    res = (
        client()
        .table("ingredient_name_curation_runs")
        .insert({"run_type": run_type, "status": "running", "config": config})
        .execute()
    )
    return res.data[0]["id"]


def _finish_run(
    run_id: str,
    status: str,
    *,
    rows_in: int,
    rows_decided: int = 0,
    rows_applied: int = 0,
    error: Exception | None = None,
) -> None:
    payload: dict[str, Any] = {
        "status": status,
        "finished_at": datetime.now().astimezone().isoformat(),
        "rows_in": rows_in,
        "rows_decided": rows_decided,
        "rows_applied": rows_applied,
    }
    if error:
        payload["error"] = f"{type(error).__name__}: {error}"[:2000]
    client().table("ingredient_name_curation_runs").update(payload).eq("id", run_id).execute()


def _fetch_existing_ingredients(page_size: int = 1000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        res = (
            client()
            .table("ingredients")
            .select("id, inci_name, normalized_name, created_at, cas_number, ec_number, iupac_name")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            return rows
        offset += page_size


def _fetch_source_verified_ingredient_ids(page_size: int = 1000) -> set[UUID]:
    ids: set[UUID] = set()
    offset = 0
    while True:
        res = (
            client()
            .table("ingredient_sources")
            .select("ingredient_id")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            ids.add(UUID(row["ingredient_id"]))
        if len(rows) < page_size:
            return ids
        offset += page_size


def _fetch_alias_collisions(normalized_name: str) -> list[dict[str, Any]]:
    res = (
        client()
        .table("ingredient_aliases")
        .select("ingredient_id, alias, normalized_alias")
        .eq("normalized_alias", normalized_name)
        .execute()
    )
    aliases = res.data or []
    if not aliases:
        return []
    ingredient_ids = [row["ingredient_id"] for row in aliases]
    ingredients = (
        client()
        .table("ingredients")
        .select("id, inci_name, normalized_name")
        .in_("id", ingredient_ids)
        .execute()
    )
    by_id = {row["id"]: row for row in ingredients.data or []}
    out = []
    for alias in aliases:
        target = by_id.get(alias["ingredient_id"], {})
        out.append({**alias, **target})
    return out


def _insert_candidate(run_id: str, row: dict[str, Any]) -> UUID:
    res = (
        client()
        .table("ingredient_name_candidates")
        .upsert(
            {
                "run_id": run_id,
                "queue_id": row["queue_id"],
                "source_ingredient_id": row["ingredient_id"],
                "inci_name": row["inci_name"],
                "normalized_name": row["normalized_name"],
                "ingredient_created_at": row.get("ingredient_created_at"),
            },
            on_conflict="run_id,source_ingredient_id",
        )
        .execute()
    )
    return UUID(res.data[0]["id"])


def _insert_evidence(
    run_id: str,
    candidate_id: UUID,
    evidence: list[IngredientEvidence],
) -> None:
    if not evidence:
        return
    client().table("ingredient_name_evidence").insert(
        [
            {
                "run_id": run_id,
                "candidate_id": str(candidate_id),
                **ev.model_dump(mode="json"),
            }
            for ev in evidence
        ]
    ).execute()


def _insert_edge(run_id: str, candidate_id: UUID, edge: dict[str, Any]) -> UUID:
    res = (
        client()
        .table("ingredient_name_edges")
        .insert({"run_id": run_id, "candidate_id": str(candidate_id), **edge})
        .execute()
    )
    return UUID(res.data[0]["id"])


def _insert_decision(
    *,
    run_id: str,
    queue_id: UUID,
    candidate_id: UUID,
    source_ingredient_id: UUID,
    decision: CurationDecision,
    decision_source: str,
) -> UUID:
    res = (
        client()
        .table("ingredient_curation_decisions")
        .upsert(
            {
                "run_id": run_id,
                "queue_id": str(queue_id),
                "candidate_id": str(candidate_id),
                "source_ingredient_id": str(source_ingredient_id),
                "target_ingredient_id": (
                    str(decision.target_ingredient_id)
                    if decision.target_ingredient_id
                    else None
                ),
                "decision": decision.decision,
                "review_status": review_status_for(decision),
                "decision_source": decision_source,
                "canonical_inci_name": decision.canonical_inci_name,
                "aliases_to_add": decision.aliases_to_add,
                "confidence": decision.confidence,
                "reason": decision.reason,
            },
            on_conflict="run_id,candidate_id,decision_source",
        )
        .execute()
    )
    return UUID(res.data[0]["id"])


def _mark_queue_after_decision(queue_id: UUID, decision: CurationDecision) -> None:
    status = "pending_human" if review_status_for(decision) == "pending_human" else "decision_ready"
    client().table("ingredient_name_curation_queue").update(
        {
            "queue_status": status,
            "processed_at": datetime.now().astimezone().isoformat(),
            "locked_at": None,
        }
    ).eq("id", str(queue_id)).execute()
