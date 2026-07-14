"""Shared fixtures: settings env and an in-memory fake of the db layer."""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")

from submission_pipeline import db as db_mod  # noqa: E402
from submission_pipeline.config import settings  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_settings():
    settings.cache_clear()
    yield
    settings.cache_clear()


class FakeDB:
    """In-memory stand-in for submission_pipeline.db."""

    def __init__(self) -> None:
        self.submissions: dict[str, dict[str, Any]] = {}
        self.tokens: dict[str, dict[str, Any]] = {}
        self.audits: list[dict[str, Any]] = []
        self.failures: list[tuple[str, str]] = []
        self.formula_matches: dict[tuple[str, ...], dict[str, Any]] = {}
        self.identity_matches: dict[tuple[str, str], dict[str, Any]] = {}
        self.ingredients: dict[str, dict[str, Any]] = {}
        self.applied: list[str] = []
        self.apply_result: str = "approved"
        self.purged: int = 0
        self.needing_description: list[dict[str, Any]] = []
        self.description_context: dict[str, dict[str, Any]] = {}
        self.descriptions: dict[str, str] = {}

    # -- seeding helpers ----------------------------------------------------

    def add_submission(self, **overrides: Any) -> dict[str, Any]:
        submission_id = overrides.pop("id", str(uuid.uuid4()))
        row = {
            "id": submission_id,
            "brand_name": "The Ordinary",
            "product_name": "Niacinamide 10% + Zinc 1%",
            "raw_ingredient_text": "Aqua, Niacinamide, Zinc PCA",
            "status": "received",
            "verification": {},
            "anthropic_batch_id": None,
            "product_id": None,
            "attempt_count": 0,
            "locked_at": None,
            **overrides,
        }
        self.submissions[submission_id] = row
        return row

    def add_token(self, submission_id: str, position: int, raw_token: str, **overrides: Any):
        token_id = overrides.pop("id", str(uuid.uuid4()))
        from submission_pipeline.normalize import normalize_name

        row = {
            "id": token_id,
            "submission_id": submission_id,
            "position": position,
            "raw_token": raw_token,
            "normalized_token": normalize_name(raw_token),
            "matched_ingredient_id": None,
            "match_type": None,
            "match_confidence": None,
            "resolution": "unresolved",
            "canonical_name": None,
            "evidence": [],
            "resolution_source": None,
            **overrides,
        }
        self.tokens[token_id] = row
        return row

    def add_catalog_product(
        self, brand_name: str, product_name: str, product_id: str | None = None
    ) -> str:
        from submission_pipeline.normalize import normalize_name

        pid = product_id or str(uuid.uuid4())
        key = (brand_name.strip().upper(), normalize_name(product_name))
        self.identity_matches[key] = {"product_id": pid, "product_name": product_name}
        return pid

    def add_ingredient(self, inci_name: str, **overrides: Any) -> dict[str, Any]:
        ingredient_id = overrides.pop("id", str(uuid.uuid4()))
        from submission_pipeline.normalize import normalize_name

        row = {
            "id": ingredient_id,
            "inci_name": inci_name,
            "normalized_name": normalize_name(inci_name),
            **overrides,
        }
        self.ingredients[ingredient_id] = row
        return row

    # -- db API -------------------------------------------------------------

    def create_submission(self, brand_name, product_name, raw_ingredient_text, submitted_by=None):
        return self.add_submission(
            brand_name=brand_name,
            product_name=product_name,
            raw_ingredient_text=raw_ingredient_text,
            submitted_by=submitted_by,
        )

    def claim_submissions(self, from_status, to_status, limit):
        claimed = []
        for row in self.submissions.values():
            if row["status"] == from_status and len(claimed) < limit:
                row["status"] = to_status
                row["attempt_count"] += 1
                claimed.append(dict(row))
        return claimed

    def fail_submission(self, submission_id, error):
        self.failures.append((submission_id, error))
        row = self.submissions[submission_id]
        max_attempts = settings().max_attempts
        row["status"] = "failed" if row["attempt_count"] >= max_attempts else "received"
        row["last_error"] = error

    def update_submission(self, submission_id, fields):
        self.submissions[submission_id].update(fields)

    def assign_batch_id(self, submission_id, batch_id):
        row = self.submissions[submission_id]
        if row["anthropic_batch_id"] is not None:
            return False
        row["anthropic_batch_id"] = batch_id
        return True

    def release_stale_claims(self, status, older_than_minutes):
        from datetime import datetime, timedelta, timezone

        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)).isoformat()
        out = {"released": 0, "failed": 0}
        max_attempts = settings().max_attempts
        for row in self.submissions.values():
            if row["status"] != status or not row.get("locked_at") or row["locked_at"] >= cutoff:
                continue
            if row["attempt_count"] >= max_attempts:
                row["status"] = "failed"
                out["failed"] += 1
            else:
                row["status"] = "received"
                out["released"] += 1
            row["locked_at"] = None
        return out

    def fetch_submissions(self, status, *, batch_id_is_null=None, limit=None):
        out = []
        for row in self.submissions.values():
            if row["status"] != status:
                continue
            if batch_id_is_null is True and row["anthropic_batch_id"] is not None:
                continue
            if batch_id_is_null is False and row["anthropic_batch_id"] is None:
                continue
            out.append(dict(row))
        return out[:limit] if limit else out

    def apply_submission(self, submission_id, actor="worker"):
        self.applied.append(submission_id)
        if self.apply_result == "raise":
            raise RuntimeError("apply blew up")
        self.submissions[submission_id]["status"] = (
            "approved" if self.apply_result == "approved" else "duplicate"
        )
        return self.apply_result

    def purge_stale(self, days):
        return self.purged

    def audit(self, submission_id, action, payload=None):
        self.audits.append(
            {"submission_id": submission_id, "action": action, "payload": payload or {}}
        )

    def replace_tokens(self, submission_id, rows):
        for token_id in [
            tid for tid, t in self.tokens.items() if t["submission_id"] == submission_id
        ]:
            del self.tokens[token_id]
        for row in rows:
            self.add_token(**{**row, "submission_id": submission_id})

    def fetch_tokens(self, submission_id):
        rows = [dict(t) for t in self.tokens.values() if t["submission_id"] == submission_id]
        return sorted(rows, key=lambda t: t["position"])

    def update_token(self, token_id, fields):
        self.tokens[token_id].update(fields)

    def find_product_formula_match(self, tokens, brand_name, product_name, similarity_threshold):
        from submission_pipeline.normalize import normalize_name

        key = tuple(normalize_name(token) for token in tokens)
        match = self.formula_matches.get(key)
        if match and (match["is_exact"] or match["similarity"] >= similarity_threshold):
            return {
                "product_name_matches": False,
                "brand_name_matches": False,
                "same_product": False,
                **match,
            }
        return None

    def find_product_by_identity(self, brand_name, product_name):
        from submission_pipeline.normalize import normalize_name

        key = (brand_name.strip().upper(), normalize_name(product_name))
        match = self.identity_matches.get(key)
        return dict(match) if match else None

    def fetch_ingredient(self, ingredient_id):
        row = self.ingredients.get(ingredient_id)
        return dict(row) if row else None

    def fetch_approved_needing_description(self, limit=50):
        return list(self.needing_description)[:limit]

    def fetch_product_description_context(self, product_id):
        return self.description_context[product_id]

    def set_product_description_if_missing(self, product_id, description):
        self.descriptions.setdefault(product_id, description)


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeDB:
    fake = FakeDB()
    for name in (
        "create_submission",
        "claim_submissions",
        "fail_submission",
        "update_submission",
        "fetch_submissions",
        "apply_submission",
        "purge_stale",
        "audit",
        "replace_tokens",
        "fetch_tokens",
        "update_token",
        "find_product_formula_match",
        "find_product_by_identity",
        "assign_batch_id",
        "release_stale_claims",
        "fetch_ingredient",
        "fetch_approved_needing_description",
        "fetch_product_description_context",
        "set_product_description_if_missing",
    ):
        monkeypatch.setattr(db_mod, name, getattr(fake, name))
    return fake


class FakeMatcher:
    """Configurable stand-in for matching.match_token."""

    def __init__(self) -> None:
        self.by_normalized: dict[str, tuple[str, str, float]] = {}

    def add(self, term: str, ingredient_id: str, match_type: str, confidence: float) -> None:
        from submission_pipeline.normalize import normalize_name

        self.by_normalized[normalize_name(term)] = (ingredient_id, match_type, confidence)

    def match_token(self, token: str):
        from submission_pipeline.matching import MatchResult
        from submission_pipeline.normalize import normalize_name

        hit = self.by_normalized.get(normalize_name(token))
        if not hit:
            return None
        ingredient_id, match_type, confidence = hit
        return MatchResult(
            ingredient_id=uuid.UUID(ingredient_id),
            match_type=match_type,
            confidence=confidence,
        )


@pytest.fixture
def fake_matcher(monkeypatch: pytest.MonkeyPatch) -> FakeMatcher:
    from submission_pipeline import matching

    fake = FakeMatcher()
    monkeypatch.setattr(matching, "match_token", fake.match_token)
    return fake


class FakeLLM:
    """Stand-in for llm.batch: records requests, serves canned results."""

    def __init__(self) -> None:
        self.submitted: list[list[dict[str, Any]]] = []
        self.statuses: dict[str, str] = {}
        self.results: dict[str, dict[str, str | None]] = {}
        self.sync_responses: list[str | None] = []
        self.next_batch_id = "batch_1"

    def submit_batch(self, requests):
        self.submitted.append(requests)
        return self.next_batch_id

    def batch_status(self, batch_id):
        return self.statuses.get(batch_id, "in_progress")

    def batch_results(self, batch_id):
        return iter(self.results.get(batch_id, {}).items())

    def sync_message(self, params):
        return self.sync_responses.pop(0) if self.sync_responses else None


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeLLM:
    from submission_pipeline.llm import batch as llm_batch

    fake = FakeLLM()
    for name in ("submit_batch", "batch_status", "batch_results", "sync_message"):
        monkeypatch.setattr(llm_batch, name, getattr(fake, name))
    return fake
