"""Verify stage: hypothesis-building guard rails."""

from __future__ import annotations

import uuid
from typing import Any

from submission_pipeline.stages import verify
from submission_pipeline.models import Hypothesis, TokenJudgment


def _token(evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "raw_token": "Weirdium Extract",
        "normalized_token": "weirdium extract",
        "matched_ingredient_id": None,
        "match_type": None,
        "match_confidence": None,
        "evidence": evidence_rows,
    }


def test_pubchem_evidence_cannot_donate_a_spelling(fake_matcher):
    token = _token(
        [
            {
                "source": "pubchem",
                "found": True,
                "canonical": "WEIRDIUM EXTRACT",
                "url": None,
                "confidence": 0.85,
            },
            {
                "source": "cosing",
                "found": True,
                "canonical": "Weirdium Extract",
                "url": None,
                "confidence": 0.97,
            },
        ]
    )
    hypotheses = verify.build_hypotheses(token)
    assert [h.source for h in hypotheses] == ["cosing"]
    assert hypotheses[0].kind == "authoritative"
    assert hypotheses[0].canonical == "Weirdium Extract"


def test_pubchem_never_enters_prompt_even_if_it_maps_to_catalog(fake_matcher):
    ingredient_id = str(uuid.uuid4())
    fake_matcher.add("Niacinamide", ingredient_id, "canonical_exact", 1.0)
    token = _token(
        [
            {
                "source": "pubchem",
                "found": True,
                "canonical": "Niacinamide",
                "confidence": 0.85,
            }
        ]
    )
    assert verify.build_hypotheses(token) == []


def test_evidence_mapping_to_catalog_becomes_existing_hypothesis(fake_matcher):
    ingredient_id = str(uuid.uuid4())
    fake_matcher.add("Water", ingredient_id, "canonical_exact", 1.0)
    token = _token(
        [
            {
                "source": "cosing",
                "found": True,
                "canonical": "Water",
                "url": None,
                "confidence": 0.97,
            }
        ]
    )
    hypotheses = verify.build_hypotheses(token)
    assert len(hypotheses) == 1
    assert hypotheses[0].kind == "existing"
    assert hypotheses[0].ingredient_id == ingredient_id


def test_spelling_sources_are_ranked_and_disagreement_is_detected(fake_matcher):
    token = _token(
        [
            {
                "source": "incidecoder",
                "found": True,
                "canonical": "Tocopherol Acetate",
                "confidence": 0.92,
            },
            {
                "source": "cosing",
                "found": True,
                "canonical": "Tocopheryl Acetate",
                "confidence": 0.97,
            },
        ]
    )
    hypotheses = verify.build_hypotheses(token)
    assert [h.source for h in hypotheses] == ["cosing", "incidecoder"]
    assert verify._has_spelling_disagreement(token)


def _existing_hypothesis() -> Hypothesis:
    return Hypothesis(
        id="fuzzy",
        kind="existing",
        canonical="Hyaluronic Acid",
        source="catalog:canonical_fuzzy",
        confidence=0.87,
        ingredient_id=str(uuid.uuid4()),
    )


def _authoritative_hypothesis() -> Hypothesis:
    return Hypothesis(
        id="evidence_0",
        kind="authoritative",
        canonical="Sodium Hyaluronate Crosspolymer",
        source="cosing",
        confidence=0.97,
    )


def test_fuzzy_match_resolves_to_existing_ingredient_only():
    hypothesis = _existing_hypothesis()
    fields = verify._judgment_fields(
        TokenJudgment("matched", "fuzzy", 0.92, "same ingredient"),
        [hypothesis],
        {"position": 8},
    )
    assert fields == {
        "resolution": "matched",
        "resolution_source": "llm",
        "matched_ingredient_id": hypothesis.ingredient_id,
    }
    assert "canonical_name" not in fields


def test_new_ingredient_uses_persisted_hypothesis_spelling():
    hypothesis = _authoritative_hypothesis()
    fields = verify._judgment_fields(
        TokenJudgment("new_ingredient", "evidence_0", 0.95, "confirmed"),
        [hypothesis],
        {"position": 8},
    )
    assert fields["resolution"] == "new_ingredient"
    assert fields["canonical_name"] == hypothesis.canonical
    assert fields["matched_ingredient_id"] is None


def test_matched_cannot_select_non_catalog_hypothesis():
    fields, trigger = verify._evaluate_judgment(
        TokenJudgment("matched", "evidence_0", 0.99, "same"),
        [_authoritative_hypothesis()],
        {"position": 8},
    )
    assert fields == {"resolution": "pending_human"}
    assert trigger == "matched_non_catalog_hypothesis"


def test_new_ingredient_cannot_select_fuzzy_catalog_hypothesis():
    fields, trigger = verify._evaluate_judgment(
        TokenJudgment("new_ingredient", "fuzzy", 0.99, "new"),
        [_existing_hypothesis()],
        {"position": 8},
    )
    assert fields == {"resolution": "pending_human"}
    assert trigger == "llm_verdict_choice_mismatch"


def test_new_ingredient_downgrades_only_when_evidence_caught_up():
    ingredient_id = str(uuid.uuid4())
    caught_up = Hypothesis(
        id="evidence_0",
        kind="existing",
        canonical="Sodium Hyaluronate Crosspolymer",
        source="cosing",
        confidence=0.97,
        ingredient_id=ingredient_id,
    )
    fields, trigger = verify._evaluate_judgment(
        TokenJudgment("new_ingredient", "evidence_0", 0.86, "catalog caught up"),
        [caught_up],
        {"position": 8},
    )
    assert fields["resolution"] == "matched"
    assert fields["matched_ingredient_id"] == ingredient_id
    assert trigger is None


def test_invalid_choice_and_low_confidence_escalate():
    fields, trigger = verify._evaluate_judgment(
        TokenJudgment("matched", "invented", 0.99, "same"),
        [_existing_hypothesis()],
        {"position": 8},
    )
    assert fields["resolution"] == "pending_human"
    assert trigger == "llm_choice_id_invalid"

    fields, trigger = verify._evaluate_judgment(
        TokenJudgment("new_ingredient", "evidence_0", 0.89, "maybe"),
        [_authoritative_hypothesis()],
        {"position": 8},
    )
    assert fields["resolution"] == "pending_human"
    assert trigger == "llm_confidence_below_threshold"


def test_junk_guard_protects_first_three_positions():
    judgment = TokenJudgment("junk", None, 0.96, "directions")
    guarded, trigger = verify._evaluate_judgment(judgment, [], {"position": 3})
    accepted, accepted_trigger = verify._evaluate_judgment(judgment, [], {"position": 4})
    assert guarded == {"resolution": "pending_human"}
    assert trigger == "junk_at_top_positions"
    assert accepted == {"resolution": "junk", "resolution_source": "llm"}
    assert accepted_trigger is None


def test_junk_with_a_choice_id_fails_closed():
    fields, trigger = verify._evaluate_judgment(
        TokenJudgment("junk", "fuzzy", 0.99, "noise"),
        [_existing_hypothesis()],
        {"position": 8},
    )
    assert fields == {"resolution": "pending_human"}
    assert trigger == "llm_choice_id_invalid"


def test_every_accepted_resolution_satisfies_apply_invariant():
    cases = [
        verify._judgment_fields(
            TokenJudgment("matched", "fuzzy", 0.95, "same"),
            [_existing_hypothesis()],
            {"position": 5},
        ),
        verify._judgment_fields(
            TokenJudgment("new_ingredient", "evidence_0", 0.95, "real"),
            [_authoritative_hypothesis()],
            {"position": 5},
        ),
        verify._judgment_fields(TokenJudgment("junk", None, 0.95, "noise"), [], {"position": 5}),
    ]
    for fields in cases:
        assert fields["resolution"] != "matched" or fields.get("matched_ingredient_id")
        assert fields["resolution"] != "new_ingredient" or fields.get("canonical_name")


def test_token_judgment_parser_fails_closed_on_shape_errors():
    assert verify.parse_token_judgment('{"verdict":"junk","confidence":0.99}').verdict == "unknown"
    assert (
        verify.parse_token_judgment(
            '{"verdict":"junk","choice_id":null,"confidence":1.2,"reason":"noise"}'
        ).verdict
        == "unknown"
    )


def test_source_disagreement_skips_token_llm_and_records_trigger(fake_db, fake_llm):
    submission = fake_db.add_submission(status="verifying")
    token = fake_db.add_token(
        submission["id"],
        5,
        "Tocopherol Acetate",
        evidence=[
            {
                "source": "cosing",
                "found": True,
                "canonical": "Tocopheryl Acetate",
                "confidence": 0.97,
            },
            {
                "source": "incidecoder",
                "found": True,
                "canonical": "Tocopherol Acetate",
                "confidence": 0.92,
            },
        ],
    )
    requests = verify._prepare_submission(submission, {"finalized": 0})
    assert [request["custom_id"] for request in requests] == [f"product_{submission['id']}"]
    assert fake_db.tokens[token["id"]]["resolution"] == "pending_human"
    assert fake_db.audits[-1]["payload"]["trigger"] == "source_disagreement"


def test_all_junk_submission_never_becomes_decision_ready(fake_db):
    submission = fake_db.add_submission(status="verifying")
    token = fake_db.add_token(submission["id"], 8, "Directions", resolution="junk")
    finding = verify.ProductFinding(
        found=True,
        source_name="Brand",
        source_url="https://brand.example/product",
        online_ingredients=[],
    )
    verify._finalize(submission["id"], [token], finding)
    assert fake_db.submissions[submission["id"]]["status"] == "pending_human"
    assert fake_db.audits[-1]["payload"]["trigger"] == "all_tokens_junk"
    assert (
        verify.parse_token_judgment(
            '{"verdict":"matched","choice_id":7,"confidence":0.99,"reason":"same"}'
        ).verdict
        == "unknown"
    )
    assert (
        verify.parse_token_judgment(
            '{"verdict":"junk","choice_id":null,"confidence":"0.99","reason":"noise"}'
        ).verdict
        == "unknown"
    )
