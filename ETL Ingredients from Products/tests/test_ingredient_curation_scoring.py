from inci_pipeline.curation.scoring import (
    NameScore,
    edit_distance,
    has_meaningful_modifier_difference,
    is_spelling_merge_candidate,
    token_overlap,
    trigram_similarity,
)


def test_edit_distance_typo():
    assert edit_distance("salycilic acid", "salicylic acid") == 2


def test_token_overlap():
    assert token_overlap("sodium hyaluronate", "hydrolyzed sodium hyaluronate") == 2 / 3


def test_modifier_guard_detects_close_distinct_names():
    assert has_meaningful_modifier_difference(
        "sodium hyaluronate",
        "hydrolyzed sodium hyaluronate",
    )


def test_spelling_candidate_allows_high_confidence_typo():
    score = NameScore(
        target_ingredient_id="00000000-0000-0000-0000-000000000001",
        target_normalized_name="salicylic acid",
        similarity=0.94,
        edit_distance=2,
        token_overlap=1.0,
        score_margin=0.20,
    )
    assert is_spelling_merge_candidate("salycilic acid", score)


def test_spelling_candidate_blocks_modifier_difference():
    score = NameScore(
        target_ingredient_id="00000000-0000-0000-0000-000000000001",
        target_normalized_name="sodium hyaluronate",
        similarity=0.93,
        edit_distance=11,
        token_overlap=2 / 3,
        score_margin=0.20,
    )
    assert not is_spelling_merge_candidate("hydrolyzed sodium hyaluronate", score)


def test_trigram_similarity_gives_typo_signal():
    assert trigram_similarity("salycilic acid", "salicylic acid") > 0.65
