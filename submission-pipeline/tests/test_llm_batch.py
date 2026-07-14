from __future__ import annotations

import pytest

from submission_pipeline.llm import batch


def test_duplicate_custom_ids_are_rejected_before_api_call():
    requests = [
        {"custom_id": "token_same", "params": {}},
        {"custom_id": "token_same", "params": {}},
    ]
    with pytest.raises(ValueError, match="duplicate custom_id"):
        batch.submit_batch(requests)
