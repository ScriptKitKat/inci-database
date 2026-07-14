"""Static contract checks for the transactional apply boundary.

The full migration chain is exercised by Supabase in integration
environments. These checks keep the safety-critical table routing visible in
the fast unit suite. Function-body assertions target the *latest* definition
of each function across all migrations (what a fresh `supabase db reset`
leaves live), so a superseding migration cannot silently drop a guard.
One-time DDL assertions stay pinned to the migration file that performs them.
"""

from __future__ import annotations

import re
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parents[2] / "supabase" / "migrations"

CLEANUP_MIGRATION = MIGRATIONS_DIR / "20260713000100_drop_legacy_data_tables.sql"
FINGERPRINT_MIGRATION = MIGRATIONS_DIR / "20260713000200_remove_product_fingerprints.sql"
FORMULA_MATCH_MIGRATION = MIGRATIONS_DIR / "20260713000300_remove_product_ingredient_metadata.sql"
NAME_AWARE_MATCH_MIGRATION = (
    MIGRATIONS_DIR / "20260713000400_name_aware_product_formula_matching.sql"
)
IDENTITY_MIGRATION = MIGRATIONS_DIR / "20260713000500_find_product_by_identity.sql"
NORMALIZE_MIGRATION = MIGRATIONS_DIR / "20260713000600_fix_inci_normalize.sql"
VERIFICATION_REVIEW_MIGRATION = (
    MIGRATIONS_DIR / "20260714000100_verification_and_curator_review.sql"
)
ATOMIC_FINALIZE_MIGRATION = (
    MIGRATIONS_DIR / "20260714000300_atomic_verification_finalize.sql"
)
RESOLVED_NAME_MIGRATION = MIGRATIONS_DIR / "20260714000400_resolved_product_names.sql"
CATALOG_SYNC_MIGRATION = MIGRATIONS_DIR / "20260714000500_sync_remote_catalog_ingredient.sql"
GLOW_RECIPE_DOMAIN_MIGRATION = (
    MIGRATIONS_DIR / "20260714000600_glow_recipe_product_domain.sql"
)
COMMON_DOMAINS_MIGRATION = MIGRATIONS_DIR / "20260714000700_common_trusted_product_domains.sql"


def _latest_function_sql(name: str) -> str:
    """The last CREATE OR REPLACE FUNCTION <name> across migrations in
    filename (i.e. apply) order — the definition that is live in production."""
    pattern = re.compile(
        rf"CREATE OR REPLACE FUNCTION {name}\s*\(.*?\$\$.*?\$\$;",
        re.DOTALL,
    )
    for path in sorted(MIGRATIONS_DIR.glob("*.sql"), reverse=True):
        matches = pattern.findall(path.read_text())
        if matches:
            return matches[-1]
    raise AssertionError(f"no migration defines {name}()")


def test_apply_writes_normalized_product_tables():
    sql = _latest_function_sql("apply_product_submission")
    assert "INSERT INTO product_ingredients (product_id, position, ingredient_id)" in sql
    assert "INSERT INTO product_ingredient_metadata" not in sql
    assert "(product_id, position, raw_inci_token, ingredient_id, is_matched)" not in sql
    assert "INSERT INTO product_metadata" not in sql


def test_new_ingredients_get_enrichment_shell_and_queue():
    sql = _latest_function_sql("apply_product_submission")
    assert "UPDATE ingredient_information" in sql
    assert "INSERT INTO ingredient_writeups" in sql
    assert "INSERT INTO ingredient_enrichment_queue" in sql


def test_apply_has_junk_and_race_guards():
    sql = _latest_function_sql("apply_product_submission")
    assert "resolution <> 'junk'" in sql
    assert "jsonb_build_object('trigger', 'all_tokens_junk')" in sql
    assert "RETURN 'pending_human'" in sql
    assert "pg_advisory_xact_lock(hashtext(v_formula_lock))" in sql
    assert "formula.ingredient_ids = v_formula_ingredient_ids" in sql
    assert "'ingredient:' || inci_normalize(t.canonical_name)" in sql


def test_apply_rejects_invalid_resolved_token_shapes():
    sql = _latest_function_sql("apply_product_submission")
    assert "resolution = 'matched'" in sql
    assert "matched_ingredient_id IS NULL" in sql
    assert "resolution = 'new_ingredient'" in sql
    assert "nullif(trim(canonical_name), '') IS NULL" in sql


def test_apply_only_collapses_same_product_identity():
    sql = _latest_function_sql("apply_product_submission")
    assert "formula.ingredient_ids = v_formula_ingredient_ids" in sql
    assert "inci_normalize(trim(p.name))" in sql
    assert "upper(trim(b.name)) = upper(trim(s.brand_name))" in sql


def test_curator_resolution_clears_incompatible_stale_fields():
    sql = _latest_function_sql("resolve_submission_token")
    assert "status = 'pending_human'" in sql
    assert "is not awaiting human review" in sql
    assert "THEN trim(p_canonical_name) ELSE NULL END" in sql
    assert "CASE WHEN p_resolution = 'matched' THEN match_type ELSE NULL END" in sql
    assert "CASE WHEN p_resolution = 'matched' THEN match_confidence ELSE NULL END" in sql


def test_catalog_label_metadata_removed_and_historical_rows_blocked():
    assert "DROP TABLE IF EXISTS product_ingredient_metadata" in FORMULA_MATCH_MIGRATION.read_text()
    # Token comparison runs on ingredient_aliases, not the dropped label table.
    assert "JOIN ingredient_aliases" in _latest_function_sql("find_product_formula_match")
    apply_sql = _latest_function_sql("apply_product_submission")
    assert "'unmatched_keep'" in apply_sql  # historical rows are blocked from approval
    resolve_sql = _latest_function_sql("resolve_submission_token")
    assert "p_resolution NOT IN ('matched', 'new_ingredient', 'junk')" in resolve_sql


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


def test_forward_matcher_is_name_and_brand_aware():
    # The signature change requires a one-time DROP of the old overload.
    assert (
        "DROP FUNCTION find_product_formula_match(TEXT[], REAL)"
        in NAME_AWARE_MATCH_MIGRATION.read_text()
    )
    sql = _latest_function_sql("find_product_formula_match")
    assert "p_similarity_threshold REAL DEFAULT 0.95" in sql
    assert "product_name_matches BOOLEAN" in sql
    assert "brand_name_matches BOOLEAN" in sql
    assert "same_product BOOLEAN" in sql
    assert "classified.is_exact AND classified.same_product" in sql
    assert "NOT classified.product_name_matches" in sql


def test_identity_lookup_mirrors_apply_name_comparison():
    sql = IDENTITY_MIGRATION.read_text()
    assert "CREATE OR REPLACE FUNCTION find_product_by_identity" in sql
    assert "upper(trim(b.name)) = upper(trim(p_brand_name))" in sql
    assert "regexp_replace(inci_normalize(trim(p.name)), '[[:space:]]+', ' ', 'g')" in sql
    assert "regexp_replace(inci_normalize(trim(p_product_name)), '[[:space:]]+', ' ', 'g')" in sql
    assert "TO service_role" in sql


def test_inci_normalize_unaccents_first_and_recomputes_stored_columns():
    sql = NORMALIZE_MIGRATION.read_text()
    # unaccent receives the raw input — transliteration happens before the
    # ASCII strip that used to destroy accented characters.
    assert "public.unaccent('public.unaccent', input)" in sql
    assert "'[^a-zA-Z0-9 ]', '', 'g'" in sql
    assert "' +', ' ', 'g'" in sql
    assert "btrim(" in sql
    assert "UPDATE ingredients SET inci_name = inci_name" in sql
    assert "UPDATE ingredient_aliases SET alias = alias" in sql
    # The fixed definition must be the live one.
    assert "btrim(" in _latest_function_sql("inci_normalize")


def test_verification_batches_are_claimed_and_attached_transactionally():
    sql = VERIFICATION_REVIEW_MIGRATION.read_text()
    assert "CREATE TABLE submission_verification_batches" in sql
    assert "FOR UPDATE SKIP LOCKED" in _latest_function_sql("claim_submission_verification")
    attach = _latest_function_sql("attach_submission_verification_batch")
    assert "status = 'verifying'" in attach
    assert "anthropic_batch_id = p_anthropic_batch_id" in attach


def test_curator_resolutions_audit_the_server_actor():
    sql = VERIFICATION_REVIEW_MIGRATION.read_text()
    assert "CREATE TABLE curator_reviewers" in sql
    resolve = _latest_function_sql("resolve_submission_token")
    assert "p_actor" in resolve
    assert "coalesce(p_actor, 'service')" in resolve


def test_verification_results_have_stale_batch_and_atomic_write_guards():
    sql = _latest_function_sql("finalize_submission_verification")
    assert "FOR UPDATE" in sql
    assert "s.anthropic_batch_id IS DISTINCT FROM p_expected_batch_id" in sql
    assert "UPDATE submission_tokens" in sql
    assert "UPDATE product_submissions" in sql
    assert "INSERT INTO submission_audit" in sql
    assert "rejection reason must be at least 10 characters" in ATOMIC_FINALIZE_MIGRATION.read_text()


def test_resolved_product_name_requires_review_and_updates_staging_name():
    sql = RESOLVED_NAME_MIGRATION.read_text()
    assert "NEW.verification ->> 'verdict' = 'name_resolved'" in sql
    assert "NEW.product_name := trim(NEW.verification ->> 'resolved_product_name')" in sql
    assert "('LA ROCHE-POSAY', 'laroche-posay.us')" in sql


def test_remote_catalog_sync_reuses_canonical_rows_and_preserves_remote_ids():
    sql = CATALOG_SYNC_MIGRATION.read_text()
    assert "WHERE normalized_name = inci_normalize(p_inci_name)" in sql
    assert "INSERT INTO ingredients (id, inci_name, slug)" in sql
    assert "VALUES (p_id, trim(p_inci_name), trim(p_slug))" in sql
    assert "TO service_role" in sql


def test_glow_recipe_official_product_domain_is_registered():
    sql = GLOW_RECIPE_DOMAIN_MIGRATION.read_text()
    assert "('GLOW RECIPE', 'glowrecipe.com')" in sql


def test_common_official_product_domains_include_kbeauty_and_makeup():
    sql = COMMON_DOMAINS_MIGRATION.read_text()
    assert sql.count("),\n") >= 75
    assert "('COSRX', 'cosrx.com')" in sql
    assert "('BEAUTY OF JOSEON', 'beautyofjoseon.com')" in sql
    assert "('RARE BEAUTY', 'rarebeauty.com')" in sql
