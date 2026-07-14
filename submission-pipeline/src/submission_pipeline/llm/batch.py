"""Anthropic Batch API helpers.

Request/response bodies are never persisted — callers keep only the
batch id and the parsed decisions (storage minimalism).
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Any

import certifi
import httpx
from anthropic import Anthropic

from ..config import settings

CUSTOM_ID_MAX_LENGTH = 64

TERMINAL_STATUSES = {"ended", "failed", "canceled", "expired"}


@lru_cache(maxsize=1)
def anthropic_client() -> Anthropic:
    s = settings()
    if not s.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return Anthropic(
        api_key=s.anthropic_api_key,
        http_client=httpx.Client(verify=certifi.where()),
    )


def reset_client() -> None:
    anthropic_client.cache_clear()


def submit_batch(requests: list[dict[str, Any]]) -> str:
    """Submit [{custom_id, params}] and return the Anthropic batch id."""
    ids = [request["custom_id"] for request in requests]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate custom_id in batch")
    for request in requests:
        if len(request["custom_id"]) > CUSTOM_ID_MAX_LENGTH:
            raise ValueError(f"custom_id too long: {request['custom_id']}")
    batch = anthropic_client().messages.batches.create(requests=requests)
    return str(_get(batch, "id"))


def batch_status(batch_id: str) -> str:
    batch = anthropic_client().messages.batches.retrieve(batch_id)
    return str(_get(batch, "processing_status") or _get(batch, "status") or "processing")


def batch_results(batch_id: str) -> Iterator[tuple[str, str | None]]:
    """Yield (custom_id, response text) pairs; text is None on errored items."""
    for result in anthropic_client().messages.batches.results(batch_id):
        yield str(_get(result, "custom_id")), _result_text(result)


def sync_message(params: dict[str, Any]) -> str | None:
    """Synchronous fallback path (used when web_search-in-batches misbehaves)."""
    message = anthropic_client().messages.create(**params)
    return _message_text(message)


def _result_text(result: Any) -> str | None:
    payload = _get(result, "result")
    if _get(payload, "type") not in {None, "succeeded"}:
        return None
    message = _get(payload, "message") or payload
    return _message_text(message)


def _message_text(message: Any) -> str | None:
    """Last text block; tool-use turns put the answer after search results."""
    content = _get(message, "content") or []
    texts = [
        _get(block, "text")
        for block in content
        if _get(block, "type") in {None, "text"} and _get(block, "text")
    ]
    return texts[-1] if texts else None


def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)
