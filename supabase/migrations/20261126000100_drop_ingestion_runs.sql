ALTER TABLE IF EXISTS public.ingredient_enrichment_decisions
  DROP CONSTRAINT IF EXISTS ingredient_enrichment_decisions_run_id_fkey,
  DROP COLUMN IF EXISTS run_id;

ALTER TABLE IF EXISTS public.ingredient_enrichment_evidence
  DROP CONSTRAINT IF EXISTS ingredient_enrichment_evidence_run_id_fkey,
  DROP COLUMN IF EXISTS run_id;

DROP TABLE IF EXISTS public.ingestion_runs CASCADE;
