"""Deterministic intake resolves safe matches and stores compact evidence."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from submission_pipeline.models import Evidence
from submission_pipeline.stages import intake


def test_exact_same_product_formula_is_marked_duplicate(fake_db, monkeypatch):
    row = fake_db.add_submission(raw_ingredient_text="Aqua, Glycerin")
    fake_db.formula_matches[("aqua", "glycerin")] = {
        "product_id": "existing-product",
        "similarity": 1.0,
        "is_exact": True,
        "product_name_matches": True,
        "brand_name_matches": True,
        "same_product": True,
    }
    # Duplicate short-circuits before the identity check.
    fake_db.add_catalog_product(row["brand_name"], row["product_name"], "existing-product")

    counters = {"claimed": 0, "queued": 0, "duplicates": 0, "human_review": 0, "failed": 0}
    intake._process(row, counters)

    assert fake_db.submissions[row["id"]]["status"] == "duplicate"
    assert fake_db.submissions[row["id"]]["product_id"] == "existing-product"
    assert not fake_db.fetch_tokens(row["id"])
    assert counters["duplicates"] == 1


def test_95_percent_different_name_formula_goes_to_human_review(fake_db, fake_matcher):
    row = fake_db.add_submission(raw_ingredient_text="Aqua, Glycerin, Panthenol")
    fake_db.formula_matches[("aqua", "glycerin", "panthenol")] = {
        "product_id": "similar-product",
        "similarity": 0.95,
        "is_exact": False,
        "product_name_matches": False,
    }

    counters = {"claimed": 0, "queued": 0, "duplicates": 0, "human_review": 0, "failed": 0}
    intake._process(row, counters)

    submission = fake_db.submissions[row["id"]]
    assert submission["status"] == "pending_human"
    assert submission["verification"]["verdict"] == "similar_product"
    assert submission["verification"]["similar_product"] == {
        "product_id": "similar-product",
        "similarity": 0.95,
    }
    assert len(fake_db.fetch_tokens(row["id"])) == 3
    assert counters["human_review"] == 1


def test_exact_different_name_formula_goes_to_human_review(fake_db, fake_matcher):
    row = fake_db.add_submission(raw_ingredient_text="Aqua, Glycerin")
    fake_db.formula_matches[("aqua", "glycerin")] = {
        "product_id": "distinct-product",
        "similarity": 1.0,
        "is_exact": True,
        "product_name_matches": False,
        "brand_name_matches": True,
        "same_product": False,
    }

    counters = {"claimed": 0, "queued": 0, "duplicates": 0, "human_review": 0, "failed": 0}
    intake._process(row, counters)

    submission = fake_db.submissions[row["id"]]
    assert submission["status"] == "pending_human"
    assert submission["product_id"] is None
    assert counters["duplicates"] == 0
    assert counters["human_review"] == 1


def test_below_95_percent_formula_continues_normal_verification(fake_db, fake_matcher):
    water = fake_db.add_ingredient("Water")
    fake_matcher.add("Aqua", water["id"], "alias_exact", 1.0)
    row = fake_db.add_submission(raw_ingredient_text="Aqua, New Extract")
    fake_db.formula_matches[("aqua", "new extract")] = {
        "product_id": "somewhat-similar-product",
        "similarity": 0.94,
        "is_exact": False,
        "product_name_matches": False,
    }

    counters = {"claimed": 0, "queued": 0, "duplicates": 0, "human_review": 0, "failed": 0}
    intake._process(row, counters)

    assert fake_db.submissions[row["id"]]["status"] == "verifying"
    assert counters["queued"] == 1
    assert counters["human_review"] == 0


def test_high_similarity_same_name_goes_to_human_review(fake_db, fake_matcher):
    row = fake_db.add_submission(raw_ingredient_text="Aqua, New Extract")
    fake_db.formula_matches[("aqua", "new extract")] = {
        "product_id": "reformulated-product",
        "similarity": 0.96,
        "is_exact": False,
        "product_name_matches": True,
        "brand_name_matches": True,
        "same_product": True,
    }
    fake_db.add_catalog_product(row["brand_name"], row["product_name"], "reformulated-product")

    counters = {"claimed": 0, "queued": 0, "duplicates": 0, "human_review": 0, "failed": 0}
    intake._process(row, counters)

    submission = fake_db.submissions[row["id"]]
    assert submission["status"] == "pending_human"
    assert submission["verification"]["verdict"] == "same_name_different_formula"
    assert submission["verification"]["existing_product"] == {
        "product_id": "reformulated-product",
        "similarity": 0.96,
    }
    assert counters["human_review"] == 1
    assert counters["queued"] == 0


def test_same_identity_with_diverged_formula_goes_to_human_review(fake_db, fake_matcher):
    """The formula matcher is blind below its similarity threshold, so the
    identity check alone must catch a same brand+name resubmission."""
    row = fake_db.add_submission(raw_ingredient_text="Aqua, New Extract")
    existing_id = fake_db.add_catalog_product(row["brand_name"], row["product_name"])

    counters = {"claimed": 0, "queued": 0, "duplicates": 0, "human_review": 0, "failed": 0}
    intake._process(row, counters)

    submission = fake_db.submissions[row["id"]]
    assert submission["status"] == "pending_human"
    assert submission["verification"]["verdict"] == "same_name_different_formula"
    assert submission["verification"]["existing_product"] == {
        "product_id": existing_id,
        "similarity": None,
    }
    assert len(fake_db.fetch_tokens(row["id"])) == 2
    assert counters["human_review"] == 1


def test_exact_same_name_different_brand_is_not_a_duplicate(fake_db, fake_matcher):
    row = fake_db.add_submission(raw_ingredient_text="Aqua, Glycerin")
    fake_db.formula_matches[("aqua", "glycerin")] = {
        "product_id": "other-brand-product",
        "similarity": 1.0,
        "is_exact": True,
        "product_name_matches": True,
        "brand_name_matches": False,
        "same_product": False,
    }

    counters = {"claimed": 0, "queued": 0, "duplicates": 0, "human_review": 0, "failed": 0}
    intake._process(row, counters)

    assert fake_db.submissions[row["id"]]["status"] == "verifying"
    assert counters["queued"] == 1
    assert counters["duplicates"] == 0


def test_exact_catalog_match_skips_evidence(fake_db, fake_matcher, monkeypatch):
    ingredient = fake_db.add_ingredient("Water")
    fake_matcher.add("Aqua", ingredient["id"], "alias_exact", 1.0)
    monkeypatch.setattr(
        intake.evidence_mod,
        "gather_evidence",
        lambda *_: (_ for _ in ()).throw(AssertionError("evidence should not run")),
    )
    row = intake._build_token_row(str(uuid.uuid4()), 1, "Aqua")
    assert row["resolution"] == "matched"
    assert row["resolution_source"] == "exact_match"


def test_evidence_stores_hits_only_and_resolves_source_to_catalog(
    fake_db, fake_matcher, monkeypatch
):
    ingredient = fake_db.add_ingredient("Panthenol")
    fake_matcher.add("Panthenol", ingredient["id"], "canonical_exact", 1.0)
    gathered = [
        Evidence(source="pubchem", found=False),
        Evidence(source="cosing", found=True, canonical="Panthenol", confidence=0.97),
    ]
    monkeypatch.setattr(intake, "_lookups", lambda: [])
    monkeypatch.setattr(intake.evidence_mod, "gather_evidence", lambda *_: gathered)
    row = intake._build_token_row(str(uuid.uuid4()), 4, "D-Panthenol")
    intake._attach_evidence(row)
    assert [item["source"] for item in row["evidence"]] == ["cosing"]
    assert row["resolution"] == "matched"
    assert row["resolution_source"] == "deterministic"
    assert row["matched_ingredient_id"] == ingredient["id"]


def test_evidence_cannot_drop_numeric_qualifier_when_matching_catalog(
    fake_db, fake_matcher, monkeypatch
):
    ingredient = fake_db.add_ingredient("Hexanediol")
    fake_matcher.add("Hexanediol", ingredient["id"], "canonical_exact", 1.0)
    gathered = [
        Evidence(source="incidecoder", found=True, canonical="Hexanediol", confidence=0.95)
    ]
    monkeypatch.setattr(intake, "_lookups", lambda: [])
    monkeypatch.setattr(intake.evidence_mod, "gather_evidence", lambda *_: gathered)
    row = intake._build_token_row(str(uuid.uuid4()), 7, "1,2-Hexanediol")

    intake._attach_evidence(row)

    assert row["resolution"] == "unresolved"
    assert row["matched_ingredient_id"] is None


def test_source_disagreement_escalates_at_intake_instead_of_resolving(
    fake_db, fake_matcher, monkeypatch
):
    """Even when one source's spelling exact-maps to the catalog, disagreeing
    INCI-native sources must reach a human, not resolve deterministically."""
    ingredient = fake_db.add_ingredient("Tocopheryl Acetate")
    fake_matcher.add("Tocopheryl Acetate", ingredient["id"], "canonical_exact", 1.0)
    gathered = [
        Evidence(source="cosing", found=True, canonical="Tocopheryl Acetate", confidence=0.97),
        Evidence(source="incidecoder", found=True, canonical="Tocopherol Acetate", confidence=0.92),
    ]
    monkeypatch.setattr(intake, "_lookups", lambda: [])
    monkeypatch.setattr(intake.evidence_mod, "gather_evidence", lambda *_: gathered)

    row = intake._build_token_row(str(uuid.uuid4()), 4, "Tocopherol Acetate")
    intake._attach_evidence(row)

    assert row["resolution"] == "pending_human"
    assert row["matched_ingredient_id"] is None
    assert fake_db.audits[-1]["action"] == "token_escalated"
    assert fake_db.audits[-1]["payload"] == {"position": 4, "trigger": "source_disagreement"}


def test_agreeing_sources_still_resolve_deterministically(fake_db, fake_matcher, monkeypatch):
    ingredient = fake_db.add_ingredient("Panthenol")
    fake_matcher.add("Panthenol", ingredient["id"], "canonical_exact", 1.0)
    gathered = [
        Evidence(source="cosing", found=True, canonical="Panthenol", confidence=0.97),
        Evidence(source="incidecoder", found=True, canonical="PANTHENOL", confidence=0.92),
    ]
    monkeypatch.setattr(intake, "_lookups", lambda: [])
    monkeypatch.setattr(intake.evidence_mod, "gather_evidence", lambda *_: gathered)

    row = intake._build_token_row(str(uuid.uuid4()), 4, "D-Panthenol")
    intake._attach_evidence(row)

    assert row["resolution"] == "matched"
    assert row["resolution_source"] == "deterministic"
    assert row["matched_ingredient_id"] == ingredient["id"]


def test_stale_triaging_claims_are_reaped_before_claiming(fake_db, monkeypatch):
    processed: list[str] = []
    monkeypatch.setattr(intake, "_process", lambda row, counters: processed.append(row["id"]))
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    stale = fake_db.add_submission(status="triaging", locked_at=old, attempt_count=1)
    exhausted = fake_db.add_submission(status="triaging", locked_at=old, attempt_count=99)
    fresh = fake_db.add_submission(
        status="triaging", locked_at=datetime.now(timezone.utc).isoformat(), attempt_count=1
    )

    counters = intake.run()

    assert fake_db.submissions[exhausted["id"]]["status"] == "failed"
    assert fake_db.submissions[fresh["id"]]["status"] == "triaging"
    # The released submission is re-claimed and processed within the same tick.
    assert stale["id"] in processed
    assert counters["stale_released"] == 1
    assert counters["stale_failed"] == 1


def test_pubchem_cannot_resolve_an_existing_catalog_row(fake_db, fake_matcher):
    ingredient = fake_db.add_ingredient("Niacinamide")
    fake_matcher.add("Niacinamide", ingredient["id"], "canonical_exact", 1.0)
    assert (
        intake._deterministic_ingredient(
            [Evidence(source="pubchem", found=True, canonical="Niacinamide", confidence=0.85)]
        )
        is None
    )
