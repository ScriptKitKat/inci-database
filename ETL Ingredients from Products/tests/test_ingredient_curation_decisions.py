from uuid import UUID

from inci_pipeline.config import settings
from inci_pipeline.curation.decisions import (
    choose_deterministic_decision,
    parse_llm_decision,
    review_status_for,
)
from inci_pipeline.curation.llm_batch import _request_payload
from inci_pipeline.curation.models import IngredientEvidence


SOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
TARGET_ID = UUID("00000000-0000-0000-0000-000000000002")


def test_canonical_collision_merges_into_existing():
    decision, edge, source = choose_deterministic_decision(
        source_ingredient_id=SOURCE_ID,
        normalized_name="sodium hyaluronate",
        canonical_collisions=[
            {
                "id": str(TARGET_ID),
                "inci_name": "Sodium Hyaluronate",
                "normalized_name": "sodium hyaluronate",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
        alias_collisions=[],
        source_evidence=[],
        spelling_scores=[],
    )
    assert decision.decision == "merge_into_existing"
    assert decision.target_ingredient_id == TARGET_ID
    assert edge is not None
    assert source == "deterministic"


def test_source_verified_name_is_kept():
    decision, edge, _ = choose_deterministic_decision(
        source_ingredient_id=SOURCE_ID,
        normalized_name="niacinamide",
        canonical_collisions=[],
        alias_collisions=[],
        source_evidence=[
            IngredientEvidence(
                source="specialchem",
                lookup_type="page",
                found=True,
                canonical_name="Niacinamide",
                normalized_canonical="niacinamide",
                confidence=0.88,
            )
        ],
        spelling_scores=[],
    )
    assert decision.decision == "keep"
    assert decision.confidence >= 0.90
    assert edge is None


def test_unverified_name_needs_human():
    decision, _, _ = choose_deterministic_decision(
        source_ingredient_id=SOURCE_ID,
        normalized_name="not found anywhere",
        canonical_collisions=[],
        alias_collisions=[],
        source_evidence=[],
        spelling_scores=[],
    )
    assert decision.decision == "needs_human"
    assert review_status_for(decision) == "pending_human"


def test_llm_malformed_json_downgrades_to_human():
    decision = parse_llm_decision("not json", {TARGET_ID})
    assert decision.decision == "needs_human"


def test_llm_unknown_target_downgrades_to_human():
    decision = parse_llm_decision(
        """
        {
          "decision": "merge_into_existing",
          "target_ingredient_id": "00000000-0000-0000-0000-000000000003",
          "canonical_inci_name": "Salicylic Acid",
          "aliases_to_add": [],
          "confidence": 0.95,
          "reason": "typo"
        }
        """,
        {TARGET_ID},
    )
    assert decision.decision == "needs_human"


def test_request_payload_uses_explicit_model_parameters():
    payload = _request_payload(
        {"candidate_id": "1", "normalized_name": "niacinamide"},
        model="claude-test-model",
        temperature=0.35,
        max_tokens=123,
    )
    assert payload["model"] == "claude-test-model"
    assert payload["temperature"] == 0.35
    assert payload["max_tokens"] == 123


def test_request_payload_uses_settings_defaults_when_not_overridden():
    s = settings()
    payload = _request_payload({"candidate_id": "1", "normalized_name": "niacinamide"})
    assert payload["model"] == s.ingredient_judge_model
    assert payload["temperature"] == s.ingredient_judge_temperature
    assert payload["max_tokens"] == s.ingredient_judge_max_tokens
