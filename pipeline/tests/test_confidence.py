from inci_pipeline.matching.confidence import KEEP_THRESHOLD, REVIEW_THRESHOLD, bucket


def test_keep_at_threshold():
    assert bucket(KEEP_THRESHOLD) == "keep"
    assert bucket(0.99) == "keep"


def test_review_band():
    assert bucket(REVIEW_THRESHOLD) == "review"
    assert bucket((KEEP_THRESHOLD + REVIEW_THRESHOLD) / 2) == "review"


def test_reject():
    assert bucket(0.0) == "reject"
    assert bucket(REVIEW_THRESHOLD - 0.01) == "reject"
