-- Remove data tables belonging to the superseded seeding and ingredient-name
-- curation pipelines. Preserve the normalized catalog tables and the new
-- product-submission verification pipeline introduced in 20260710000100.

-- Remove legacy hooks on preserved tables before dropping their queue tables.
DROP TRIGGER IF EXISTS trg_enqueue_ingredient_name_curation ON ingredients;

DROP FUNCTION IF EXISTS enqueue_ingredient_name_curation();
DROP FUNCTION IF EXISTS enqueue_ingredient_name_curation_window(TIMESTAMPTZ, TIMESTAMPTZ);
DROP FUNCTION IF EXISTS claim_ingredient_name_curation_queue(INTEGER);
DROP FUNCTION IF EXISTS fail_ingredient_name_curation_queue(UUID, TEXT, INTEGER);
DROP FUNCTION IF EXISTS apply_ingredient_curation_decision(UUID);

-- Legacy ingredient-name curation pipeline, child tables first.
DROP TABLE IF EXISTS ingredient_curation_apply_audit;
DROP TABLE IF EXISTS ingredient_llm_batch_items;
DROP TABLE IF EXISTS ingredient_curation_decisions;
DROP TABLE IF EXISTS ingredient_name_evidence;
DROP TABLE IF EXISTS ingredient_name_edges;
DROP TABLE IF EXISTS ingredient_name_candidates;
DROP TABLE IF EXISTS ingredient_llm_batches;
DROP TABLE IF EXISTS ingredient_name_curation_queue;
DROP TABLE IF EXISTS ingredient_name_curation_runs;

-- Other legacy data and metadata tables.
DROP TABLE IF EXISTS ingredient_curation_queue;
DROP TABLE IF EXISTS ingredient_sources;
DROP TABLE IF EXISTS ingestion_runs;
