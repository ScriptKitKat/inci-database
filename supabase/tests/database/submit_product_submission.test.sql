BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SELECT plan(18);

INSERT INTO auth.users (id, email) VALUES
  ('10000000-0000-0000-0000-000000000001', 'submitter@example.com'),
  ('10000000-0000-0000-0000-000000000002', 'other@example.com');

SET LOCAL ROLE anon;
SELECT throws_ok(
  $$ SELECT submit_product_submission('Acme', 'Serum', 'Water, Glycerin') $$,
  '42501', NULL, 'anonymous callers cannot submit'
);
RESET ROLE;

SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims = '{"sub":"10000000-0000-0000-0000-000000000001","role":"authenticated"}';

SELECT lives_ok(
  $$ CREATE TEMP TABLE first_submission AS
     SELECT submit_product_submission(' Acme ', ' Serum ', ' Water, Glycerin ') AS id $$,
  'a signed-in user can submit a product'
);
SELECT is(
  submit_product_submission('acme', 'serum', 'Water, Glycerin'),
  (SELECT id FROM first_submission),
  'retrying an in-flight submission returns the same id'
);
SELECT is(
  submit_product_submission('Acme', 'Serum', 'Water,  Glycerin'),
  (SELECT id FROM first_submission),
  'whitespace-collapsed ingredient text returns the same in-flight id'
);
SELECT throws_ok(
  $$ SELECT submit_product_submission('', 'Serum', 'Water') $$,
  '22023', 'brand name must be 1-200 characters', 'blank brand is rejected'
);
SELECT throws_ok(
  $$ SELECT submit_product_submission('Acme', 'Serum', repeat('x', 20001)) $$,
  '22023', 'ingredient list must be 1-20000 characters', 'oversized label is rejected'
);
SELECT throws_ok(
  $$ INSERT INTO product_submissions (submitted_by, brand_name, product_name, raw_ingredient_text, status)
     VALUES ('10000000-0000-0000-0000-000000000001', 'Acme', 'Serum', 'Water', 'approved') $$,
  '42501', NULL, 'direct inserts cannot forge submission state'
);
SELECT results_eq(
  $$ SELECT brand_name, product_name, status FROM product_submissions $$,
  $$ VALUES ('Acme'::TEXT, 'Serum'::TEXT, 'received'::TEXT) $$,
  'submitters read their own trimmed submission and its status'
);
SELECT throws_ok(
  $$ SELECT verification FROM product_submissions $$,
  '42501', NULL, 'internal verification details stay private'
);
SELECT throws_ok(
  $$ SELECT 1 FROM submission_tokens $$,
  '42501', NULL, 'submitters cannot read staging tokens'
);

SET LOCAL request.jwt.claims = '{"sub":"10000000-0000-0000-0000-000000000002","role":"authenticated"}';
SELECT is_empty(
  $$ SELECT id FROM product_submissions $$,
  'other users cannot see the submission'
);
RESET ROLE;

SELECT results_eq(
  $$ SELECT submitted_by, status FROM product_submissions $$,
  $$ VALUES ('10000000-0000-0000-0000-000000000001'::UUID, 'received'::TEXT) $$,
  'exactly one received row is recorded for the submitter'
);
SELECT results_eq(
  $$ SELECT action, actor FROM submission_audit $$,
  $$ VALUES ('submitted'::TEXT, '10000000-0000-0000-0000-000000000001'::TEXT) $$,
  'the submission is audited with the submitter id'
);
SELECT throws_ok(
  $$ INSERT INTO product_submissions (submitted_by, brand_name, product_name, raw_ingredient_text)
     VALUES ('10000000-0000-0000-0000-000000000001', 'acme', 'serum', 'Water,  Glycerin') $$,
  '23505', NULL, 'open submissions are unique per submitter and fingerprint'
);

UPDATE product_submissions
SET status = 'approved'
WHERE id = (SELECT id FROM first_submission);

SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims = '{"sub":"10000000-0000-0000-0000-000000000001","role":"authenticated"}';
SELECT lives_ok(
  $$ CREATE TEMP TABLE after_approve AS
     SELECT submit_product_submission('Acme', 'Serum', 'Water, Glycerin') AS id $$,
  'the same product can be submitted again after the prior one is no longer open'
);
SELECT isnt(
  (SELECT id FROM after_approve),
  (SELECT id FROM first_submission),
  'a completed prior submission does not reuse the old id'
);

SET LOCAL request.jwt.claims = '{"sub":"10000000-0000-0000-0000-000000000002","role":"authenticated"}';
SELECT lives_ok(
  $$ CREATE TEMP TABLE other_user_submission AS
     SELECT submit_product_submission('Acme', 'Serum', 'Water, Glycerin') AS id $$,
  'a second user can submit the same product independently'
);
SELECT isnt(
  (SELECT id FROM other_user_submission),
  (SELECT id FROM after_approve),
  'another user receives their own submission id'
);

SELECT * FROM finish();
ROLLBACK;
