BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SELECT plan(3);

SELECT is(
  enum_range(NULL::public.ingredient_rating)::TEXT,
  '{ew_ew,okie,yippe,wowza}',
  'fresh migration replay produces exactly the live rating labels in order'
);
SELECT col_type_is(
  'public', 'ingredient_information', 'rating', 'ingredient_rating',
  'the rating column uses the canonical enum'
);
SELECT ok(
  to_regtype('public.ingredient_rating_legacy') IS NULL,
  'the legacy enum is removed without leftover types'
);

SELECT * FROM finish();
ROLLBACK;
