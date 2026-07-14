"""Static contract checks for the transactional apply boundary.

The full migration is exercised by Supabase in integration environments. These
checks keep the safety-critical table routing visible in the fast unit suite.
"""

from pathlib import Path


CLEANUP_MIGRATION = (
    Path(__file__).parents[2]
    / "supabase"
    / "migrations"
    / "20260713000100_drop_legacy_data_tables.sql"
)
FINGERPRINT_MIGRATION = (
    Path(__file__).parents[2]
    / "supabase"
    / "migrations"
    / "20260713000200_remove_product_fingerprints.sql"
)
FORMULA_MATCH_MIGRATION = (
    Path(__file__).parents[2]
    / "supabase"
    / "migrations"
    / "20260713000300_remove_product_ingredient_metadata.sql"
)
NAME_AWARE_MATCH_MIGRATION = (
    Path(__file__).parents[2]
    / "supabase"
    / "migrations"
    / "20260713000400_name_aware_product_formula_matching.sql"
)


def _formula_sql() -> str:
    return FORMULA_MATCH_MIGRATION.read_text()


def test_apply_writes_normalized_product_tables():
    sql = _formula_sql()
    assert "INSERT INTO product_ingredients (product_id, position, ingredient_id)" in sql
    assert "INSERT INTO product_ingredient_metadata" not in sql
    assert "(product_id, position, raw_inci_token, ingredient_id, is_matched)" not in sql
    assert "INSERT INTO product_metadata" not in sql


def test_new_ingredients_get_enrichment_shell_and_queue():
    sql = _formula_sql()
    assert "UPDATE ingredient_information" in sql
    assert "INSERT INTO ingredient_writeups" in sql
    assert "INSERT INTO ingredient_enrichment_queue" in sql


def test_apply_has_junk_and_race_guards():
    sql = _formula_sql()
    assert "resolution <> 'junk'" in sql
    assert "jsonb_build_object('trigger', 'all_tokens_junk')" in sql
    assert "RETURN 'pending_human'" in sql
    assert "pg_advisory_xact_lock(hashtext(v_formula_lock))" in sql
    assert "formula.ingredient_ids = v_formula_ingredient_ids" in sql
    assert "'ingredient:' || inci_normalize(t.canonical_name)" in sql


def test_apply_rejects_invalid_resolved_token_shapes():
    sql = _formula_sql()
    assert "resolution = 'matched'" in sql
    assert "matched_ingredient_id IS NULL" in sql
    assert "resolution = 'new_ingredient'" in sql
    assert "nullif(trim(canonical_name), '') IS NULL" in sql


def test_curator_resolution_clears_incompatible_stale_fields():
    sql = _formula_sql()
    assert "status = 'pending_human'" in sql
    assert "is not awaiting human review" in sql
    assert "THEN trim(p_canonical_name) ELSE NULL END" in sql
    assert "CASE WHEN p_resolution = 'matched' THEN match_type ELSE NULL END" in sql
    assert "CASE WHEN p_resolution = 'matched' THEN match_confidence ELSE NULL END" in sql


def test_later_cleanup_preserves_submission_and_normalized_metadata_tables():
    sql = CLEANUP_MIGRATION.read_text()
    preserved = (
        "product_submissions",
        "submission_tokens",
        "submission_audit",
        "curators",
        "product_ingredient_metadata",
    )
    for table in preserved:
        assert f"DROP TABLE IF EXISTS {table}" not in sql
    assert "DROP FUNCTION IF EXISTS is_curator" not in sql
    assert "DROP FUNCTION IF EXISTS apply_product_submission" not in sql


def test_forward_migration_removes_stored_fingerprints():
    sql = FINGERPRINT_MIGRATION.read_text()
    assert "CREATE OR REPLACE FUNCTION find_product_formula_match" in sql
    assert "DROP COLUMN IF EXISTS ingredient_fingerprint" in sql
    assert "DROP TABLE IF EXISTS product_metadata" in sql


def test_latest_migration_removes_catalog_label_metadata():
    sql = _formula_sql()
    assert "DROP TABLE IF EXISTS product_ingredient_metadata" in sql
    assert "JOIN ingredient_aliases" in sql
    assert "p_resolution NOT IN ('matched', 'new_ingredient', 'junk')" in sql
    assert "'unmatched_keep'" in sql  # historical rows are blocked from approval


def test_forward_matcher_is_name_and_brand_aware():
    sql = NAME_AWARE_MATCH_MIGRATION.read_text()
    assert "DROP FUNCTION find_product_formula_match(TEXT[], REAL)" in sql
    assert "p_similarity_threshold REAL DEFAULT 0.95" in sql
    assert "product_name_matches BOOLEAN" in sql
    assert "brand_name_matches BOOLEAN" in sql
    assert "same_product BOOLEAN" in sql
    assert "classified.is_exact AND classified.same_product" in sql
    assert "NOT classified.product_name_matches" in sql


def test_apply_only_collapses_same_product_identity():
    sql = NAME_AWARE_MATCH_MIGRATION.read_text()
    assert "formula.ingredient_ids = v_formula_ingredient_ids" in sql
    assert "inci_normalize(trim(p.name))" in sql
    assert "upper(trim(b.name)) = upper(trim(s.brand_name))" in sql
