BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SELECT plan(14);

SELECT col_not_null('public', 'ingredient_information', 'cosing_information',
  'CosIng information is non-nullable');
SELECT col_default_is('public', 'ingredient_information', 'cosing_information', '{}'::jsonb,
  'CosIng information defaults to an empty object');
SELECT has_index('public', 'ingredient_information', 'ingredient_information_cosing_gin',
  'CosIng information has a GIN index');
SELECT has_index('public', 'ingredient_information', 'ingredient_information_cas_idx',
  'CosIng CAS numbers have an expression index');
SELECT ok(
  NOT has_function_privilege('anon', 'apply_product_submission(uuid,text)', 'EXECUTE')
  AND NOT has_function_privilege('authenticated', 'apply_product_submission(uuid,text)', 'EXECUTE')
  AND has_function_privilege('service_role', 'apply_product_submission(uuid,text)', 'EXECUTE'),
  'approval remains restricted to the service role'
);

INSERT INTO product_submissions
  (id, brand_name, product_name, raw_ingredient_text, status, verification)
VALUES (
  '30000000-0000-0000-0000-000000000001', 'CosIng Test', 'Lip Liner',
  'Cosing Test Extract, Uncertain Test Extract', 'pending_human',
  '{"verdict":"uncertain","online_verified":false}'::jsonb
);
INSERT INTO submission_tokens
  (submission_id, position, raw_token, normalized_token, resolution,
   resolution_source, canonical_name, evidence)
VALUES
  ('30000000-0000-0000-0000-000000000001', 1, 'Cosing Test Extract',
   'cosing test extract', 'new_ingredient', 'human', 'Cosing Test Extract',
   '[{"source":"cosing","found":false,"enrichment":{"cas_number":"ignored"}},
     {"source":"cosing","found":true,"enrichment":{"cas_number":"123-45-6","description":"Test extract"}},
     {"source":"cosing","found":true,"enrichment":{"cas_number":"also ignored"}}]'::jsonb),
  ('30000000-0000-0000-0000-000000000001', 2, 'Uncertain Test Extract',
   'uncertain test extract', 'new_ingredient', 'human', 'Uncertain Test Extract', '[]'::jsonb);

SET LOCAL ROLE service_role;
SELECT is(
  apply_product_submission('30000000-0000-0000-0000-000000000001', 'curator'),
  'approved', 'human approval creates ingredients despite uncertain online verification'
);
RESET ROLE;
SELECT is(
  (SELECT info.cosing_information FROM ingredient_information info
   JOIN ingredients i ON i.id = info.ingredient_id WHERE i.inci_name = 'Cosing Test Extract'),
  '{"cas_number":"123-45-6","description":"Test extract"}'::jsonb,
  'the information row retains the first found CosIng enrichment'
);
SELECT is(
  (SELECT info.cosing_information FROM ingredient_information info
   JOIN ingredients i ON i.id = info.ingredient_id WHERE i.inci_name = 'Uncertain Test Extract'),
  '{}'::jsonb, 'an ingredient without CosIng evidence still has an information row'
);
SELECT is(
  (SELECT count(*)::INTEGER FROM ingredients i
   JOIN ingredient_information info ON info.id = i.ingredient_information_id
     AND info.ingredient_id = i.id
   WHERE i.inci_name IN ('Cosing Test Extract', 'Uncertain Test Extract')),
  2, 'both new ingredients keep their information pointers'
);
SELECT is(
  (SELECT count(*)::INTEGER FROM ingredient_writeups w
   JOIN ingredients i ON i.id = w.ingredient_id
   WHERE i.inci_name IN ('Cosing Test Extract', 'Uncertain Test Extract')
     AND w.editorial_metadata ->> 'status' = 'draft'),
  2, 'both new ingredients receive draft writeups'
);
SELECT is(
  (SELECT count(*)::INTEGER FROM ingredient_enrichment_queue q
   JOIN ingredients i ON i.id = q.ingredient_id
   WHERE i.inci_name IN ('Cosing Test Extract', 'Uncertain Test Extract')),
  2, 'both new ingredients are queued for enrichment'
);
SELECT is(
  (SELECT count(*)::INTEGER FROM product_ingredients pi
   JOIN product_submissions s ON s.product_id = pi.product_id
   WHERE s.id = '30000000-0000-0000-0000-000000000001'),
  2, 'the approved product retains both ingredients'
);
SELECT throws_ok(
  $$ UPDATE ingredient_information SET cosing_information = '[]'::jsonb $$,
  '23514', NULL, 'the restored constraint rejects non-object CosIng data'
);
SELECT throws_ok(
  $$ UPDATE ingredient_information SET cosing_information = NULL $$,
  '23502', NULL, 'the restored column rejects null CosIng data'
);

SELECT * FROM finish();
ROLLBACK;
