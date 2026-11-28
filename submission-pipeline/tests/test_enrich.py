import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from submission_pipeline import cli, db
from submission_pipeline.config import settings
from submission_pipeline.enrichment import parse_enrichment, review_reason
from submission_pipeline.stages import enrich


@pytest.fixture
def payload():
    return {
        "rating": "yippe",
        "functions": ["humectant"],
        "quick_facts": ["Retains moisture"],
        "summary": "A humectant.",
        "details": "Helps retain water.",
        "confidence": 0.9,
        "rationale": "Supported by supplied evidence.",
    }


@pytest.fixture
def context():
    return {
        "inci_name": "Glycerin",
        "aliases": ["Glycerol"],
        "information": {"cosing_information": {"description": "Glycerol"}},
        "allowed_functions": ["humectant"],
        "sources": [],
        "writeup": {},
    }


def test_valid(payload):
    result = parse_enrichment(json.dumps(payload), ["humectant"])
    assert result.model_dump() == payload
    assert review_reason(result, 0.8) is None


@pytest.mark.parametrize(
    "change",
    [
        {"rating": 5},
        {"rating": "great"},
        {"rating": "superhero"},
        {"functions": ["made-up"]},
        {"extra": "forbidden"},
        {"confidence": 1.1},
        {"confidence": -0.1},
        {"confidence": True},
        {"confidence": "0.9"},
        {"confidence": float("nan")},
        {"summary": " "},
        {"summary": "a" * 2001},
        {"details": "a" * 10001},
        {"quick_facts": ["a"] * 11},
        {"quick_facts": ["a", "a"]},
        {"functions": [1]},
        {"rationale": "a" * 501},
    ],
)
def test_invalid(payload, change):
    assert parse_enrichment(json.dumps(payload | change), ["humectant"]) is None


@pytest.mark.parametrize("text", ["", "not json", "{}", "```json\n{}\n```", "{} trailing"])
def test_parse_failure(text):
    assert parse_enrichment(text, []) is None
    assert review_reason(None, 0.8) == "invalid_enrichment_result"


def test_unknown_fields_are_nullable(payload):
    for key in ("rating", "functions", "quick_facts", "summary", "details"):
        payload[key] = None
    assert parse_enrichment(json.dumps(payload), []) is not None


def test_low_confidence(payload):
    result = parse_enrichment(json.dumps(payload | {"confidence": 0.79}), ["humectant"])
    assert review_reason(result, 0.8) == "enrichment_confidence_below_threshold"
    assert review_reason(result, 0.79) is None


def test_request_and_prompt(context):
    request = enrich.build_request({"ingredient_id": "abc"}, context)
    assert request["custom_id"] == "enrich_abc"
    assert request["params"]["model"] == settings().describe_model
    text = request["params"]["messages"][0]["content"]
    assert "{{" not in text
    assert json.dumps(context) in text
    assert "wowza" in text and "rather than guess" in text


@pytest.fixture
def queue(monkeypatch, context):
    state = SimpleNamespace(rows=[], applied=[], reviews=[], failed=[], limits=[])

    def claim(claim_id, limit):
        state.limits.append(limit)
        rows = [r for r in state.rows if r.get("claim_id") is None and not r.get("done")][:limit]
        for row in rows:
            row["claim_id"] = claim_id
        return [dict(r) for r in rows]

    def attach(claim_id, batch_id, count):
        rows = [r for r in state.rows if r.get("claim_id") == claim_id]
        assert len(rows) == count
        for row in rows:
            row["anthropic_batch_id"] = batch_id

    def finish(row, value, target):
        target.append((row["ingredient_id"], value))
        next(r for r in state.rows if r["ingredient_id"] == row["ingredient_id"])["done"] = True

    monkeypatch.setattr(db, "claim_enrichment", claim)
    monkeypatch.setattr(
        db,
        "fetch_enrichment_batches",
        lambda: [dict(r) for r in state.rows if r.get("anthropic_batch_id") and not r.get("done")],
    )
    monkeypatch.setattr(db, "fetch_enrichment_context", lambda _: context)
    monkeypatch.setattr(db, "attach_enrichment_batch", attach)
    monkeypatch.setattr(db, "apply_enrichment", lambda r, p: finish(r, p, state.applied))
    monkeypatch.setattr(db, "review_enrichment", lambda r, p: finish(r, p, state.reviews))
    monkeypatch.setattr(db, "fail_enrichment", lambda r, p: finish(r, p, state.failed))
    return state


def test_across_ticks(queue, fake_llm, payload):
    queue.rows = [{"ingredient_id": "one"}]
    assert enrich.run()["submitted"] == 1
    assert not queue.applied
    assert enrich.run()["waiting"] == 1
    assert len(fake_llm.submitted) == 1
    fake_llm.statuses["batch_1"] = "ended"
    fake_llm.results["batch_1"] = {"enrich_one": json.dumps(payload)}
    assert enrich.run()["applied"] == 1
    assert queue.applied == [("one", payload)]
    assert not queue.reviews


@pytest.mark.parametrize(
    "response,reason",
    [("invalid", "invalid_enrichment_result"), ("low", "enrichment_confidence_below_threshold")],
)
def test_review(queue, fake_llm, payload, response, reason):
    queue.rows = [{"ingredient_id": "one"}]
    enrich.run()
    fake_llm.statuses["batch_1"] = "ended"
    fake_llm.results["batch_1"] = {
        "enrich_one": "bad json"
        if response == "invalid"
        else json.dumps(payload | {"confidence": 0.2})
    }
    assert enrich.run()["review"] == 1
    assert queue.reviews == [("one", reason)]
    assert not queue.applied


@pytest.mark.parametrize("status", ["failed", "canceled", "expired", "ended"])
def test_errored_batch(queue, fake_llm, status):
    queue.rows = [{"ingredient_id": "one"}]
    enrich.run()
    fake_llm.statuses["batch_1"] = status
    assert enrich.run()["failed"] == 1
    assert len(queue.failed) == 1


def test_cap(queue, fake_llm, monkeypatch):
    monkeypatch.setenv("ENRICH_CLAIM_LIMIT", "2")
    queue.rows = [{"ingredient_id": str(i)} for i in range(5)]
    assert enrich.run()["submitted"] == 2
    assert len(fake_llm.submitted[0]) == 2
    assert queue.limits == [2]


def test_submit_failure(queue, fake_llm, monkeypatch):
    queue.rows = [{"ingredient_id": "one"}]

    def fail(_):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(enrich.llm_batch, "submit_batch", fail)
    assert enrich.run()["failed"] == 1
    assert queue.failed


def test_poll_lookup_failure_keeps_batch(queue, fake_llm, monkeypatch):
    queue.rows = [{"ingredient_id": "one"}]
    enrich.run()

    def fail(_):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(enrich.llm_batch, "batch_status", fail)
    assert enrich.run()["waiting"] == 1
    assert not queue.failed
    assert len(fake_llm.submitted) == 1


def test_cli_wiring(monkeypatch):
    assert cli.STAGE_ORDER == (
        "poll",
        "intake",
        "submit_batch",
        "apply",
        "describe",
        "enrich",
        "purge",
    )
    assert cli._stages()["enrich"] is enrich.run
    monkeypatch.setattr(enrich, "run", lambda: {"submitted": 2})
    result = CliRunner().invoke(cli.app, ["run", "--stage", "enrich"])
    assert result.exit_code == 0
    assert "enrich: {'submitted': 2}" in result.stdout
    assert "enrich" in CliRunner().invoke(cli.app, ["run", "--help"]).stdout
