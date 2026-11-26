from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

log = logging.getLogger(__name__)


@contextmanager
def log_stage_run(
    stage: str, metadata: dict[str, Any] | None = None
) -> Iterator[dict[str, int]]:
    counters = {"rows_in": 0, "rows_upserted": 0}
    log.info("%s started: %s", stage, metadata or {})
    try:
        yield counters
    except Exception:
        log.error("%s failed: %s", stage, counters)
        raise
    else:
        log.info("%s completed: %s", stage, counters)
