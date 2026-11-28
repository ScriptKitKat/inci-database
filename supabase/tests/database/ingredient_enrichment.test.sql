BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS dblink WITH SCHEMA extensions;
SELECT no_plan();

DELETE FROM ingredient_enrichment_queue;
INSERT INTO ingredients (id, inci_name, slug) VALUES
  ('40000000-0000-0000-0000-000000000001', 'Enrichment One', 'enrichment-one'),
  ('40000000-0000-0000-0000-000000000002', 'Enrichment Curated', 'enrichment-curated'),
  ('40000000-0000-0000-0000-000000000003', 'Enrichment Partial', 'enrichment-partial'),
  ('40000000-0000-0000-0000-000000000004', 'Enrichment Exhausted', 'enrichment-exhausted');
UPDATE ingredient_information SET rating = 'wowza', functions = ARRAY['humectant','emollient'],
  cosing_information = '{"description":"Curated evidence"}', additional_information = '{"preserve":true}'
WHERE ingredient_id = '40000000-0000-0000-0000-000000000002';
INSERT INTO ingredient_writeups (ingredient_id, quick_facts, summary, details, editorial_metadata)
VALUES ('40000000-0000-0000-0000-000000000002', ARRAY['Curated fact'],
  'Curated summary', 'Curated details', '{"status":"published","language":"en"}');
INSERT INTO ingredient_enrichment_queue (ingredient_id, status, attempt_count) VALUES
  ('40000000-0000-0000-0000-000000000001', 'unfilled', 0),
  ('40000000-0000-0000-0000-000000000002', 'ingredient_description_filled', 0),
  ('40000000-0000-0000-0000-000000000003', 'ingredient_information_filled', 0),
  ('40000000-0000-0000-0000-000000000004', 'unfilled', 3);
CREATE TEMP TABLE enrichment_payload AS SELECT '{"rating":"yippe","functions":["humectant"],
 "quick_facts":["Retains moisture"],"summary":"A humectant.","details":"Helps retain water.",
 "confidence":0.9,"rationale":"Evidence supplied"}'::jsonb AS value;

SELECT is((SELECT count(*)::int FROM claim_ingredient_enrichment(
  '41000000-0000-0000-0000-000000000001', 1)), 1, 'claims at most the cap');
SELECT is((SELECT status FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000004'), 'pending_human', 'exhausted rows are parked');
SELECT is((SELECT count(*)::int FROM claim_ingredient_enrichment(
  '41000000-0000-0000-0000-000000000001', 1)), 1, 'repeating a claim is idempotent');
SELECT is((SELECT count(*)::int FROM ingredient_enrichment_queue WHERE claim_id =
  '41000000-0000-0000-0000-000000000001'), 1, 'repeating claim does not take more rows');
SELECT ok(NOT EXISTS(SELECT 1 FROM ingredient_enrichment_queue
  WHERE status IN ('pending_human', 'ingredient_description_filled') AND claim_id IS NOT NULL),
  'only unfinished eligible rows are claimed');
SELECT lives_ok($$SELECT attach_ingredient_enrichment_batch(
  '41000000-0000-0000-0000-000000000001', 'test-batch', 1)$$, 'batch attached');
SELECT is((SELECT count(*)::int FROM fetch_ingredient_enrichment_batches()), 1, 'in-flight batch is pollable');
SELECT lives_ok($$SELECT attach_ingredient_enrichment_batch(
  '41000000-0000-0000-0000-000000000001', 'test-batch', 1)$$, 'batch attach is idempotent');
SELECT throws_ok($$SELECT attach_ingredient_enrichment_batch(
  '41000000-0000-0000-0000-000000000001', 'different-batch', 1)$$,
  'P0001', 'stale enrichment claim', 'cannot replace an in-flight batch');

UPDATE ingredient_enrichment_queue SET locked_at = now() - interval '31 minutes'
  WHERE claim_id IS NOT NULL;
SELECT count(*) FROM claim_ingredient_enrichment('41000000-0000-0000-0000-000000000002', 10);
SELECT is((SELECT anthropic_batch_id FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000001'), 'test-batch', 'normal batch latency does not release claim');
UPDATE ingredient_enrichment_queue SET locked_at = now() - interval '31 minutes'
  WHERE claim_id = '41000000-0000-0000-0000-000000000002';
SELECT count(*) FROM claim_ingredient_enrichment('41000000-0000-0000-0000-000000000003', 10);
SELECT is((SELECT attempt_count FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000003'), 1, 'stale preparation increments attempts');
UPDATE ingredient_enrichment_queue SET locked_at = now() - interval '49 hours'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000001';
SELECT count(*) FROM claim_ingredient_enrichment('41000000-0000-0000-0000-000000000004', 10);
SELECT is((SELECT attempt_count FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000001'), 1, 'abandoned attached batch is recovered');
SELECT throws_ok($$SELECT apply_ingredient_enrichment('40000000-0000-0000-0000-000000000001',
  '41000000-0000-0000-0000-000000000001', (SELECT value FROM enrichment_payload))$$,
  'P0001', 'stale enrichment claim', 'stale result cannot write');
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000001',
  '41000000-0000-0000-0000-000000000004', (SELECT value FROM enrichment_payload)),
  'ingredient_description_filled', 'both complete parts advance to description filled');
SELECT is((SELECT rating::text FROM ingredient_information WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000001'), 'yippe', 'fills missing canonical rating');
SELECT is((SELECT functions FROM ingredient_information WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000001'), ARRAY['humectant'], 'fills missing functions');
SELECT is((SELECT editorial_metadata->>'status' FROM ingredient_writeups WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000001'), 'draft', 'new writeup remains draft');
SELECT ok((SELECT claim_id IS NULL AND anthropic_batch_id IS NULL AND locked_at IS NULL
  FROM ingredient_enrichment_queue WHERE ingredient_id = '40000000-0000-0000-0000-000000000001'),
  'completion clears claim and batch');
CREATE TEMP TABLE enrichment_snapshot AS SELECT to_jsonb(w) AS value FROM ingredient_writeups w
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000001';
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000001',
  '41000000-0000-0000-0000-000000000004', (SELECT value FROM enrichment_payload)),
  'ingredient_description_filled', 'repeated apply is idempotent');
SELECT is((SELECT to_jsonb(w) FROM ingredient_writeups w WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000001'), (SELECT value FROM enrichment_snapshot),
  'repeated apply does not even change timestamps');

UPDATE ingredient_enrichment_queue SET status = 'unfilled',
  claim_id = '41000000-0000-0000-0000-000000000005' WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000002';
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000002',
  '41000000-0000-0000-0000-000000000005', (SELECT value FROM enrichment_payload)),
  'ingredient_description_filled', 'curated ingredient completes without overwrites');
SELECT is((SELECT rating::text FROM ingredient_information WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000002'), 'wowza', 'curated rating preserved');
SELECT is((SELECT functions FROM ingredient_information WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000002'), ARRAY['humectant','emollient'], 'curated functions preserved');
SELECT is((SELECT summary FROM ingredient_writeups WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000002'), 'Curated summary', 'curated summary preserved');
SELECT is((SELECT details FROM ingredient_writeups WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000002'), 'Curated details', 'curated details preserved');
SELECT is((SELECT quick_facts FROM ingredient_writeups WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000002'), ARRAY['Curated fact'], 'curated facts preserved');
SELECT is((SELECT editorial_metadata FROM ingredient_writeups WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000002'), '{"status":"published","language":"en"}'::jsonb,
  'existing editorial metadata preserved');
SELECT is((ingredient_enrichment_context('40000000-0000-0000-0000-000000000002')
  ->'information'->'additional_information'), '{"preserve":true}'::jsonb, 'existing evidence preserved');
SELECT is((ingredient_enrichment_context('40000000-0000-0000-0000-000000000002')
  ->'allowed_functions'), '["emollient","humectant"]'::jsonb, 'vocabulary comes from existing catalog');

SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000003',
  '41000000-0000-0000-0000-000000000003', (SELECT value || '{"summary":null,"details":null,"quick_facts":null}'
  FROM enrichment_payload)), 'ingredient_information_filled', 'structured-only output stays in first phase');
SELECT count(*) FROM claim_ingredient_enrichment('41000000-0000-0000-0000-000000000006', 10);
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000003',
  '41000000-0000-0000-0000-000000000006', (SELECT value || '{"confidence":0.2}' FROM enrichment_payload)),
  'pending_human', 'low confidence enters human review');
SELECT ok((SELECT summary IS NULL AND details IS NULL FROM ingredient_writeups WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000003'), 'low confidence writes no editorial content');
SELECT is((SELECT review_reason FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000003'), 'enrichment_confidence_below_threshold', 'review reason stored');

UPDATE ingredient_enrichment_queue SET status = 'unfilled', attempt_count = 0,
  claim_id = '41000000-0000-0000-0000-000000000007'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000004';
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000004',
  '41000000-0000-0000-0000-000000000007', (SELECT value || '{"functions":["invented"]}' FROM enrichment_payload)),
  'pending_human', 'unknown function is reviewed');
SELECT ok((SELECT rating IS NULL AND functions = '{}' FROM ingredient_information WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000004'), 'invalid output writes no live information');
UPDATE ingredient_enrichment_queue SET status = 'unfilled', attempt_count = 2,
  claim_id = '41000000-0000-0000-0000-000000000007'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000004';
SELECT fail_ingredient_enrichment('40000000-0000-0000-0000-000000000004',
  '41000000-0000-0000-0000-000000000007', 'test failure');
SELECT is((SELECT attempt_count FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000004'), 3, 'failure increments attempt count');
SELECT is((SELECT status FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000004'), 'pending_human', 'failure at attempt cap parks row');
SELECT fail_ingredient_enrichment('40000000-0000-0000-0000-000000000004',
  '41000000-0000-0000-0000-000000000007', 'duplicate failure');
SELECT is((SELECT attempt_count FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000004'), 3, 'repeated failure is idempotent');

UPDATE ingredient_enrichment_queue SET status = 'unfilled', attempt_count = 0,
  claim_id = '41000000-0000-0000-0000-000000000007'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000004';
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000004',
  '41000000-0000-0000-0000-000000000007', (SELECT value || '{"rating":5}' FROM enrichment_payload)),
  'pending_human', 'numeric rating is rejected');
UPDATE ingredient_enrichment_queue SET status = 'unfilled',
  claim_id = '41000000-0000-0000-0000-000000000007'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000004';
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000004',
  '41000000-0000-0000-0000-000000000007', (SELECT value || '{"extra":true}' FROM enrichment_payload)),
  'pending_human', 'unknown keys are rejected');
UPDATE ingredient_enrichment_queue SET status = 'unfilled',
  claim_id = '41000000-0000-0000-0000-000000000007'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000004';
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000004',
  '41000000-0000-0000-0000-000000000007', (SELECT value || '{"confidence":"invalid"}' FROM enrichment_payload)),
  'pending_human', 'nonnumeric confidence is rejected');
UPDATE ingredient_enrichment_queue SET status = 'unfilled', attempt_count = 2,
  claim_id = '41000000-0000-0000-0000-000000000007', locked_at = now() - interval '31 minutes'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000004';
SELECT count(*) FROM claim_ingredient_enrichment('41000000-0000-0000-0000-000000000008', 10);
SELECT is((SELECT status FROM ingredient_enrichment_queue WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000004'), 'pending_human', 'stale release honors attempt cap');
UPDATE ingredient_enrichment_queue SET status = 'unfilled', attempt_count = 0,
  claim_id = '41000000-0000-0000-0000-000000000007'
  WHERE ingredient_id = '40000000-0000-0000-0000-000000000004';
INSERT INTO ingredient_writeups (ingredient_id, summary, details)
VALUES ('40000000-0000-0000-0000-000000000004', '', ' ');
SELECT is(apply_ingredient_enrichment('40000000-0000-0000-0000-000000000004',
  '41000000-0000-0000-0000-000000000007', (SELECT value FROM enrichment_payload)),
  'ingredient_description_filled', 'blank strings and empty arrays are filled');
SELECT is((SELECT summary FROM ingredient_writeups WHERE ingredient_id =
  '40000000-0000-0000-0000-000000000004'), 'A humectant.', 'blank summary replaced');

SELECT dblink_connect('enrichment_locker', 'host=supabase_db_inci-database dbname=postgres user=postgres password=postgres');
SELECT dblink_exec('enrichment_locker', $$INSERT INTO ingredients (id, inci_name, slug)
  VALUES ('40000000-0000-0000-0000-000000000099', 'Enrichment Locked', 'enrichment-locked')$$);
SELECT dblink_exec('enrichment_locker', $$INSERT INTO ingredient_enrichment_queue (ingredient_id)
  VALUES ('40000000-0000-0000-0000-000000000099')$$);
SELECT dblink_exec('enrichment_locker', 'BEGIN');
SELECT dblink_exec('enrichment_locker', $$DO $lock$ BEGIN
  PERFORM 1 FROM ingredient_enrichment_queue WHERE ingredient_id =
    '40000000-0000-0000-0000-000000000099' FOR UPDATE; END $lock$;$$);
SELECT is((SELECT count(*)::int FROM claim_ingredient_enrichment(
  '41000000-0000-0000-0000-000000000008', 10)), 0, 'locked eligible row is skipped without blocking');
SELECT dblink_exec('enrichment_locker', 'ROLLBACK');
SELECT dblink_exec('enrichment_locker', $$DELETE FROM ingredients
  WHERE id = '40000000-0000-0000-0000-000000000099'$$);
SELECT dblink_disconnect('enrichment_locker');

SET LOCAL ROLE anon;
SELECT throws_ok($$SELECT claim_ingredient_enrichment(gen_random_uuid())$$,
  '42501', 'permission denied for function claim_ingredient_enrichment', 'anon cannot claim');
SELECT throws_ok($$SELECT apply_ingredient_enrichment(gen_random_uuid(), gen_random_uuid(), '{}')$$,
  '42501', 'permission denied for function apply_ingredient_enrichment', 'anon cannot apply');
RESET ROLE;
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub', '42000000-0000-0000-0000-000000000001', true);
SELECT throws_ok($$SELECT claim_ingredient_enrichment(gen_random_uuid())$$,
  'P0001', 'not authorized: curator role required', 'non-curator cannot claim');
SELECT throws_ok($$SELECT apply_ingredient_enrichment(gen_random_uuid(), gen_random_uuid(), '{}')$$,
  'P0001', 'not authorized: curator role required', 'non-curator cannot apply');
SELECT throws_ok($$SELECT fail_ingredient_enrichment(gen_random_uuid(), gen_random_uuid(), 'x')$$,
  'P0001', 'not authorized: curator role required', 'non-curator cannot fail');
SELECT throws_ok($$SELECT review_ingredient_enrichment(gen_random_uuid(), gen_random_uuid(), 'x')$$,
  'P0001', 'not authorized: curator role required', 'non-curator cannot review');
SELECT throws_ok($$SELECT ingredient_enrichment_context(gen_random_uuid())$$,
  'P0001', 'not authorized: curator role required', 'non-curator cannot read worker evidence');
SELECT throws_ok($$SELECT fetch_ingredient_enrichment_batches()$$,
  'P0001', 'not authorized: curator role required', 'non-curator cannot poll');
SELECT throws_ok($$SELECT attach_ingredient_enrichment_batch(gen_random_uuid(), 'batch', 1)$$,
  'P0001', 'not authorized: curator role required', 'non-curator cannot attach batch');
RESET ROLE;
SELECT * FROM finish();
ROLLBACK;
