-- Fix inci_normalize: the previous definition stripped non-ASCII characters
-- BEFORE unaccent ran, so unaccent was dead code ('Karité' -> 'karit' instead
-- of 'karite'), and it never collapsed the whitespace left behind by stripping
-- punctuation ('Parfum / Fragrance' -> 'parfum  fragrance').
--
-- New order: transliterate accents first, then strip to [a-zA-Z0-9 ], lower,
-- collapse runs of spaces, trim.
CREATE OR REPLACE FUNCTION inci_normalize(input text)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
STRICT
AS $$
  SELECT btrim(
    regexp_replace(
      lower(
        regexp_replace(
          public.unaccent('public.unaccent', input),
          '[^a-zA-Z0-9 ]', '', 'g'
        )
      ),
      ' +', ' ', 'g'
    )
  );
$$;

-- Redefining an IMMUTABLE function does not rewrite existing STORED generated
-- columns; no-op updates force every row's normalized value to be recomputed
-- under the fixed definition. The normalized columns carry no UNIQUE
-- constraints, so the recompute cannot collide.
UPDATE ingredients SET inci_name = inci_name;
UPDATE ingredient_aliases SET alias = alias;
