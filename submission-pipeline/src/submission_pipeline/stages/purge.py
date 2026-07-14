"""Purge stage: drop rejected/duplicate submissions past retention."""

from __future__ import annotations

from .. import db
from ..config import settings


def run() -> dict[str, int]:
    return {"purged": db.purge_stale(settings().purge_days)}
