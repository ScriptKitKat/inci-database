"""Confidence helpers used when classifying matches as keep / review."""

from __future__ import annotations

KEEP_THRESHOLD = 0.92
REVIEW_THRESHOLD = 0.80


def bucket(confidence: float) -> str:
    if confidence >= KEEP_THRESHOLD:
        return "keep"
    if confidence >= REVIEW_THRESHOLD:
        return "review"
    return "reject"
