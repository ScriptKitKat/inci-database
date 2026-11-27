BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SELECT plan(8);

INSERT INTO ingredients (id, inci_name, slug) VALUES
  ('20000000-0000-0000-0000-0000000000a1', 'Water', 'water'),
  ('20000000-0000-0000-0000-0000000000a2', 'Glycerin', 'glycerin');

INSERT INTO product_submissions (id, brand_name, product_name, raw_ingredient_text, status) VALUES
  ('20000000-0000-0000-0000-000000000001', 'Acme', 'Dew Serum', 'Water, Zorblax Extract', 'decision_ready'),
  ('20000000-0000-0000-0000-000000000002', 'Acme', 'Dew Serum', 'Water, Zorblax Extract', 'decision_ready'),
  ('20000000-0000-0000-0000-000000000003', 'ACME', 'dew  serum', 'Water, Glycerin', 'decision_ready');

INSERT INTO submission_tokens
  (submission_id, position, raw_token, normalized_token, matched_ingredient_id,
   resolution, resolution_source, canonical_name)
SELECT id, 1, 'Water', 'water', '20000000-0000-0000-0000-0000000000a1'::UUID,
       'matched', 'exact_match', NULL
FROM product_submissions
UNION ALL
SELECT id, 2, 'Zorblax Extract', 'zorblax extract', NULL,
       'new_ingredient', 'llm', 'Zorblax Extract'
FROM product_submissions WHERE raw_ingredient_text LIKE '%Zorblax%'
UNION ALL
SELECT '20000000-0000-0000-0000-000000000003', 2, 'Glycerin', 'glycerin',
       '20000000-0000-0000-0000-0000000000a2'::UUID, 'matched', 'exact_match', NULL;

SET LOCAL ROLE service_role;

SELECT is(
  apply_product_submission('20000000-0000-0000-0000-000000000001'),
  'approved', 'the first submission creates the product and its new ingredient'
);
SELECT is(
  apply_product_submission('20000000-0000-0000-0000-000000000002'),
  'duplicate', 'an identical submission introducing the same new ingredient is a duplicate'
);
SELECT is(
  (SELECT product_id FROM product_submissions WHERE id = '20000000-0000-0000-0000-000000000002'),
  (SELECT product_id FROM product_submissions WHERE id = '20000000-0000-0000-0000-000000000001'),
  'the duplicate points at the existing product'
);
SELECT is(
  apply_product_submission('20000000-0000-0000-0000-000000000003'),
  'pending_human', 'a same-name product with a different formula is escalated, not auto-created'
);
SELECT results_eq(
  $$ SELECT verification ->> 'verdict', verification -> 'existing_product' ->> 'product_id'
     FROM product_submissions WHERE id = '20000000-0000-0000-0000-000000000003' $$,
  $$ SELECT 'same_name_different_formula'::TEXT, product_id::TEXT
     FROM product_submissions WHERE id = '20000000-0000-0000-0000-000000000001' $$,
  'the escalation names the conflicting catalog product for the curator'
);
SELECT is(
  apply_product_submission('20000000-0000-0000-0000-000000000003', 'Priscilla'),
  'approved', 'a curator approving after seeing the conflict creates the reformulation'
);
SELECT is(
  (SELECT count(*)::INTEGER FROM products p JOIN brands b ON b.id = p.brand_id
   WHERE b.normalized = 'ACME'),
  2, 'only the curator-approved reformulation adds a second product'
);
SELECT is(
  (SELECT count(*)::INTEGER FROM ingredients WHERE inci_name = 'Zorblax Extract'),
  1, 'the new ingredient is created once'
);

RESET ROLE;
SELECT * FROM finish();
ROLLBACK;
