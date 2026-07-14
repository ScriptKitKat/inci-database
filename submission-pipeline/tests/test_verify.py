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


def test_submit_assigns_batch_id_to_batched_submissions(fake_db, fake_llm):
    submission = fake_db.add_submission(status="verifying")
    fake_db.add_token(submission["id"], 1, "Weirdium Extract")

    counters = verify.submit()

    assert fake_db.submissions[submission["id"]]["anthropic_batch_id"] == "batch_1"
    assert counters["submissions"] == 1
    assert counters["batches"] == 1
    assert next(iter(fake_db.verification_batches.values()))["status"] == "submitted"


def test_claim_prevents_a_second_worker_from_batching_same_submission(fake_db, fake_llm):
    submission = fake_db.add_submission(status="verifying")
    fake_db.add_token(submission["id"], 1, "Weirdium Extract")

    first = verify.submit()
    second = verify.submit()

    assert first["submissions"] == 1
    assert second["submissions"] == 0
    assert len(fake_llm.submitted) == 1


def test_product_finding_requires_safe_complete_shape():
    assert verify.parse_product_finding(
        '{"found":true,"source_name":"Brand","source_url":"http://brand.test/p",'
        '"online_ingredients":[],"reason":"Exact product."}'
    ) is None
    assert verify.parse_product_finding(
        '{"found":true,"source_name":"Brand","source_url":"https://user:pass@brand.test/p",'
        '"online_ingredients":[],"reason":"Exact product."}'
    ) is None
    not_found = verify.parse_product_finding(
        '{"found":false,"source_name":"Contradiction","source_url":"https://bad.test",'
        '"online_ingredients":["Guessed"],"reason":"No exact page."}'
    )
    assert not_found == verify.ProductFinding(found=False, reason="No exact page.")


def test_trusted_matching_formula_resolves_generic_product_name_to_human(fake_db):
    submission = fake_db.add_submission(
        status="verifying", brand_name="La Roche-Posay", product_name="Sun Screen"
    )
    fake_db.brand_domains["LA ROCHE-POSAY"] = ["laroche-posay.us"]
    tokens = [
        fake_db.add_token(submission["id"], 1, "Titanium Dioxide", resolution="matched"),
        fake_db.add_token(submission["id"], 2, "Water", resolution="matched"),
    ]
    finding = verify.ProductFinding(
        found=True,
        matched_product_name="Anthelios Mineral Tinted Sunscreen for Face with SPF",
        source_name="La Roche-Posay",
        source_url="https://www.laroche-posay.us/anthelios-mineral-tinted.html",
        online_ingredients=["Titanium Dioxide", "Water"],
        reason="Published formula matches.",
    )

    verify._finalize(
        submission["id"], tokens, finding, submitted_product_name=submission["product_name"]
    )

    row = fake_db.submissions[submission["id"]]
    assert row["status"] == "pending_human"
    assert row["product_name"] == "Anthelios Mineral Tinted Sunscreen for Face with SPF"
    assert row["verification"]["verdict"] == "name_resolved"
    assert row["verification"]["submitted_product_name"] == "Sun Screen"
    assert fake_db.audits[-1]["payload"]["trigger"] == "product_name_resolved"


def test_resolved_product_name_remains_primary_review_trigger_with_pending_tokens():
    assert (
        verify._submission_trigger("name_resolved", True, False, [])
        == "product_name_resolved"
    )


def test_published_name_with_leading_brand_is_not_a_rename():
    assert not verify._should_resolve_product_name(
        "Watermelon Glow Niacinamide Dew Drops",
        "Glow Recipe Watermelon Glow Niacinamide Dew Drops",
        "Glow Recipe",
    )


def test_trusted_product_host_requires_exact_domain_or_subdomain(fake_db, monkeypatch):
    submission = fake_db.add_submission()
    monkeypatch.setenv("TRUSTED_PRODUCT_DOMAINS", "sephora.com")
    from submission_pipeline.config import settings

    settings.cache_clear()
    assert verify.is_trusted_product_url(submission["id"], "https://www.sephora.com/p/item")
    assert not verify.is_trusted_product_url(
        submission["id"], "https://sephora.com.example.org/p/item"
    )


def test_olive_young_is_a_globally_trusted_retailer(fake_db):
    submission = fake_db.add_submission()
    assert verify.is_trusted_product_url(
        submission["id"], "https://global.oliveyoung.com/product/detail"
    )


def test_overlap_is_bidirectional_one_to_one_and_handles_water_alternatives():
    assert verify.coverage(["Water (Aqua/Eau)", "Glycerin"], ["Aqua", "glycerin!"]) == (
        1.0,
        1.0,
    )
    assert verify.coverage(["Water", "Aqua"], ["Eau"]) == (0.5, 1.0)
    assert verify.coverage(["Water"], ["Aqua", "Glycerin"]) == (1.0, 0.5)


def test_more_descriptive_submitted_product_name_is_not_treated_as_a_rename():
    submitted = (
        "Cicapair™ Sensitive Skin Korean Face Moisturizer for Redness "
        "with Centella Asiatica"
    )
    published = "Cicapair Sensitive Skin Moisturizer for Redness"

    assert not verify._should_resolve_product_name(submitted, published)
    assert verify._should_resolve_product_name(
        "Sun Screen", "Anthelios Mineral Tinted Sunscreen for Face with SPF"
    )


def test_trusted_matching_product_formula_supplies_new_ingredient_spellings(fake_db):
    submission = fake_db.add_submission(status="verifying")
    token = fake_db.add_token(submission["id"], 1, "WATER/AQUA/EAU")
    finding = verify.ProductFinding(
        found=True,
        source_name="Sephora",
        source_url="https://www.sephora.com/product/example",
        online_ingredients=["Water"],
        reason="Published formula matches.",
    )

    names = verify._trusted_formula_canonical_names(
        submission["id"], [token], finding
    )

    assert names == {token["id"]: "Water"}


def test_matching_trusted_formula_auto_resolves_tokens_without_human_review(fake_db):
    product_name = (
        "Cicapair™ Sensitive Skin Korean Face Moisturizer for Redness "
        "with Centella Asiatica"
    )
    submission = fake_db.add_submission(status="verifying", product_name=product_name)
    water = fake_db.add_token(submission["id"], 1, "WATER/AQUA/EAU")
    hexanediol = fake_db.add_token(submission["id"], 2, "1,2-HEXANEDIOL")
    result = (
        '{"found":true,"matched_product_name":"Cicapair Sensitive Skin '
        'Moisturizer for Redness","source_name":"Sephora","source_url":'
        '"https://www.sephora.com/product/cicapair","online_ingredients":'
        '["Water","1,2-Hexanediol"],"reason":"Published formula matches."}'
    )

    verify._apply_results(submission, {f"product_{submission['id']}": result})

    row = fake_db.submissions[submission["id"]]
    assert row["status"] == "decision_ready"
    assert row["verification"]["verdict"] == "verified"
    assert fake_db.tokens[water["id"]]["canonical_name"] == "Water"
    assert fake_db.tokens[hexanediol["id"]]["canonical_name"] == "1,2-Hexanediol"


def test_untrusted_product_source_routes_to_human(fake_db):
    submission = fake_db.add_submission(status="verifying")
    token = fake_db.add_token(submission["id"], 1, "Water", resolution="matched")
    verify._finalize(
        submission["id"],
        [token],
        verify.ProductFinding(
            found=True,
            source_name="Unknown",
            source_url="https://unapproved.example/product",
            online_ingredients=["Water"],
            reason="Exact page.",
        ),
    )
    row = fake_db.submissions[submission["id"]]
    assert row["status"] == "pending_human"
    assert row["verification"]["verdict"] == "untrusted_source"


def test_batch_limits_never_split_one_submission(fake_db, fake_llm, monkeypatch):
    monkeypatch.setenv("VERIFICATION_BATCH_MAX_REQUESTS", "3")
    from submission_pipeline.config import settings

    settings.cache_clear()
    for name in ("One", "Two"):
        submission = fake_db.add_submission(status="verifying", product_name=name)
        fake_db.add_token(submission["id"], 1, f"{name} Extract")

    counters = verify.submit()

    assert counters["batches"] == 2
    assert [len(requests) for requests in fake_llm.submitted] == [2, 2]


def test_oversized_submission_goes_to_human_without_partial_batch(
    fake_db, fake_llm, monkeypatch
):
    monkeypatch.setenv("VERIFICATION_BATCH_MAX_REQUESTS", "1")
    from submission_pipeline.config import settings

    settings.cache_clear()
    submission = fake_db.add_submission(status="verifying")
    fake_db.add_token(submission["id"], 1, "Unresolved")

    counters = verify.submit()

    assert counters["oversized"] == 1
    assert fake_llm.submitted == []
    assert fake_db.submissions[submission["id"]]["status"] == "pending_human"
    assert fake_db.audits[-1]["payload"]["trigger"] == "submission_too_large"


def test_two_terminal_batch_failures_enable_sync_product_fallback(fake_db, fake_llm):
    submission = fake_db.add_submission(
        status="verifying", attempt_count=2, anthropic_batch_id="batch_failed"
    )
    token = fake_db.add_token(submission["id"], 4, "Unresolved")
    fake_db.verification_batches["group"] = {
        "id": "group",
        "anthropic_batch_id": "batch_failed",
        "submission_ids": [submission["id"]],
        "request_count": 2,
        "payload_bytes": 100,
        "status": "submitted",
    }
    fake_llm.statuses["batch_failed"] = "expired"

    verify.poll()

    retried = fake_db.submissions[submission["id"]]
    assert retried["verification"]["sync_product_verification"] is True
    fake_llm.sync_responses.append(
        '{"found":false,"source_name":null,"source_url":null,'
        '"online_ingredients":[],"reason":"No exact product page."}'
    )
    requests = verify._prepare_submission(retried, {"finalized": 0})
    assert [request["custom_id"] for request in requests] == [f"token_{token['id']}"]
