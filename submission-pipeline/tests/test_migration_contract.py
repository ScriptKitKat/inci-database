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
BATCH_MATCH_MIGRATION = MIGRATIONS_DIR / "20261125050730_match_ingredients_batch.sql"
BATCH_MATCH_LIMIT_MIGRATION = MIGRATIONS_DIR / "20261125051301_limit_ingredient_match_batch.sql"
CURATED_SEEDER_GRANTS_MIGRATION = MIGRATIONS_DIR / "20261125051302_curated_seeder_insert_grants.sql"
CURATORS_RATE_LIMITS_MIGRATION = MIGRATIONS_DIR / "20261126210438_drop_curators_rate_limits.sql"
SUBMIT_RPC_MIGRATION = MIGRATIONS_DIR / "20261127000100_submit_product_submission_rpc.sql"
COSING_REPAIR_MIGRATION = (
    MIGRATIONS_DIR / "20261128000200_restore_ingredient_cosing_information.sql"
)


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


def test_expanded_cosing_functions_preserve_distinct_roles():
    sql = _latest_function_sql("public.ingredient_functions_are_valid")
    assert "'propellant'" in sql
    assert "'hair_conditioning'" in sql
    assert "'skin_conditioning'" in sql
    assert "'uv_absorber'" in sql
    assert "'uv_filtering'" in sql
    assert "'surfactant'" in sql
    assert "'surfactant_cleansing'" in sql
    assert "'not_reported'" not in sql


def test_new_ingredients_get_enrichment_shell_and_queue():
    sql = _latest_function_sql("apply_product_submission")
    assert "information_schema" not in sql
    assert "SELECT coalesce(e.value -> 'enrichment', '{}'::jsonb)" in sql
    assert "WHERE e.value ->> 'source' = 'cosing'" in sql
    assert "AND coalesce((e.value ->> 'found')::boolean, false)" in sql
    assert (
        "UPDATE ingredient_information\n"
        "      SET cosing_information = cosing_information || coalesce(v_cosing, '{}'::jsonb),"
    ) in sql
    assert "WHERE ingredient_id = v_ingredient" in sql
    assert "INSERT INTO ingredient_writeups" in sql
    assert "INSERT INTO ingredient_enrichment_queue" in sql


def test_cosing_repair_guarantees_schema_before_redefining_apply():
    sql = COSING_REPAIR_MIGRATION.read_text()
    schema, apply = sql.split("CREATE OR REPLACE FUNCTION apply_product_submission", 1)
    assert "ALTER TABLE public.ingredient_information" in schema
    assert "ADD COLUMN IF NOT EXISTS cosing_information JSONB NOT NULL DEFAULT '{}'::jsonb" in schema
    assert "IF NOT EXISTS" in schema
    assert "FROM pg_catalog.pg_constraint" in schema
    assert "conrelid = 'public.ingredient_information'::regclass" in schema
    assert "conname = 'ingredient_information_cosing_information_check'" in schema
    assert "ADD CONSTRAINT ingredient_information_cosing_information_check" in schema
    assert "CHECK (jsonb_typeof(cosing_information) = 'object')" in schema
    assert "CREATE INDEX IF NOT EXISTS ingredient_information_cosing_gin" in schema
    assert "USING GIN (cosing_information)" in schema
    assert "CREATE INDEX IF NOT EXISTS ingredient_information_cas_idx" in schema
    assert "((cosing_information ->> 'cas_number'))" in schema
    assert "WHERE cosing_information ? 'cas_number'" in schema
    assert _latest_function_sql("apply_product_submission") in sql
    assert "LANGUAGE plpgsql SECURITY DEFINER\nSET search_path = public" in apply
    assert (
        "REVOKE EXECUTE ON FUNCTION apply_product_submission(UUID, TEXT)\n"
        "  FROM PUBLIC, anon, authenticated;"
    ) in apply
    assert "GRANT EXECUTE ON FUNCTION apply_product_submission(UUID, TEXT) TO service_role;" in apply


def test_apply_has_junk_and_race_guards():
    sql = _latest_function_sql("apply_product_submission")
    assert "resolution <> 'junk'" in sql
    assert "jsonb_build_object('trigger', 'all_tokens_junk')" in sql
    assert "RETURN 'pending_human'" in sql
    assert "'product:' || v_brand_norm" in sql
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


def test_apply_escalates_unreviewed_same_identity_products():
    sql = _latest_function_sql("apply_product_submission")
    assert "i.normalized_name = inci_normalize(st.canonical_name)" in sql
    assert "find_product_by_identity(s.brand_name, s.product_name)" in sql
    assert "'same_name_different_formula'" in sql


def test_end_users_submit_only_through_the_validated_rpc():
    sql = SUBMIT_RPC_MIGRATION.read_text()
    assert "DROP POLICY IF EXISTS submissions_insert_own" in sql
    assert "GRANT EXECUTE ON FUNCTION public.submit_product_submission(TEXT, TEXT, TEXT)\n  TO authenticated" in sql
    assert "GRANT INSERT" not in sql
    assert "verification" not in sql.split("GRANT SELECT", 1)[1]


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


def test_unused_curator_and_rate_limit_tables_drop_without_changing_submissions():
    sql = CURATORS_RATE_LIMITS_MIGRATION.read_text()
    assert "DROP FUNCTION IF EXISTS public.consume_request_rate_limit(TEXT, INTEGER, INTEGER);" in sql
    assert re.findall(r"DROP TABLE IF EXISTS (.+?);", sql) == [
        "public.request_rate_limits",
        "public.curators",
    ]
    is_curator = _latest_function_sql("public.is_curator")
    assert is_curator in sql
    assert "LANGUAGE sql STABLE SECURITY DEFINER" in is_curator
    assert "SELECT false;" in is_curator
    assert "IF auth.uid() IS NOT NULL AND NOT is_curator()" in _latest_function_sql(
        "assert_curator_or_service"
    )


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


def test_batch_ingredient_match_exposes_ordered_non_nullable_matches_to_api_roles():
    for migration in (BATCH_MATCH_MIGRATION, BATCH_MATCH_LIMIT_MIGRATION):
        sql = migration.read_text()
        assert "public.match_ingredients_batch(inputs TEXT[])" in sql
        assert "RETURNS TABLE (input_token TEXT, ingredient_id UUID, match_type TEXT, confidence REAL)" in sql
        assert "unnest(inputs) WITH ORDINALITY" in sql
        assert "CROSS JOIN LATERAL public.match_ingredient(requested.token)" in sql
        assert "ORDER BY requested.ord" in sql
    assert "TO anon, authenticated, service_role" in BATCH_MATCH_MIGRATION.read_text()


def test_batch_ingredient_match_rejects_oversized_inputs_before_matching():
    sql = BATCH_MATCH_LIMIT_MIGRATION.read_text()
    assert "IF cardinality(inputs) > 50 THEN" in sql
    assert "USING ERRCODE = '22023'" in sql
    assert sql.index("IF cardinality(inputs)") < sql.index("public.match_ingredient(requested.token)")


def test_curated_seeder_grants_only_required_insert_columns():
    sql = CURATED_SEEDER_GRANTS_MIGRATION.read_text()
    assert sql.count("GRANT ") == 3
    assert "GRANT INSERT (name, slug) ON public.brands TO service_role;" in sql
    assert "INSERT (name, slug, brand_id, short_description) ON public.products TO service_role;" in sql
    assert "INSERT (product_id, ingredient_id, position) ON public.product_ingredients TO service_role;" in sql


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


def test_ingredient_enrichment_has_guarded_atomic_rpc_boundaries():
    migration = MIGRATIONS_DIR / "20261128000300_ingredient_enrichment.sql"
    sql = migration.read_text()
    for name in ("ingredient_enrichment_context", "claim_ingredient_enrichment",
                 "attach_ingredient_enrichment_batch", "fetch_ingredient_enrichment_batches",
                 "apply_ingredient_enrichment", "fail_ingredient_enrichment",
                 "review_ingredient_enrichment"):
        definition = _latest_function_sql(f"public.{name}")
        assert "SECURITY DEFINER" in definition
        assert "SET search_path = public" in definition
        assert "PERFORM assert_curator_or_service()" in definition
        assert f"REVOKE ALL ON FUNCTION public.{name}" in sql
        assert f"GRANT EXECUTE ON FUNCTION public.{name}" in sql
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "p_claim_id" in sql and "stale_enrichment_claim" in sql
    assert "'pending_human'" in sql
    assert "request_body" not in sql and "response_body" not in sql
    assert "'ingredient_information_filled'" in sql
    assert "'ingredient_description_filled'" in sql


def test_ingredient_enrichment_ddl_tolerates_schema_drift():
    migration = MIGRATIONS_DIR / "20261128000300_ingredient_enrichment.sql"
    schema = migration.read_text().split("CREATE OR REPLACE FUNCTION", 1)[0]
    assert "CREATE TABLE IF NOT EXISTS public.ingredient_enrichment_queue" in schema
    assert "CREATE INDEX IF NOT EXISTS ingredient_enrichment_queue_status_idx" in schema
    for column in ("anthropic_batch_id", "claim_id", "locked_at", "attempt_count", "review_reason"):
        assert f"ADD COLUMN IF NOT EXISTS {column}" in schema
    assert "ALTER COLUMN attempt_count SET DEFAULT 0" in schema
    assert "ALTER COLUMN attempt_count SET NOT NULL" in schema
    assert "SET attempt_count = 0 WHERE attempt_count IS NULL" in schema
    assert "FROM pg_catalog.pg_constraint" in schema
    assert "c.conrelid = 'public.ingredient_enrichment_queue'::regclass" in schema
    assert "c.contype = 'c'" in schema
    assert "a.attnum = ANY(c.conkey)" in schema
    assert "a.attname = 'status'" in schema
    assert "FOR v_constraint IN" in schema
    assert "DROP CONSTRAINT %I" in schema
    assert "DROP CONSTRAINT ingredient_enrichment_queue_status_check" not in schema
    assert "ADD CONSTRAINT ingredient_enrichment_queue_status_check" in schema
    assert "CHECK (attempt_count >= 0)" in schema
    assert "CHECK (length(review_reason) <= 500)" in schema
