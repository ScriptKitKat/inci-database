BEGIN;

SET LOCAL statement_timeout = '10min';

CREATE TABLE IF NOT EXISTS product_ingredient_cleanup_findings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_label TEXT NOT NULL,
  reason TEXT NOT NULL,
  action TEXT NOT NULL,
  raw_inci_token TEXT,
  row_count INTEGER NOT NULL,
  example_context JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TEMP TABLE bad_text_patterns (
  pattern TEXT PRIMARY KEY,
  reason TEXT NOT NULL
) ON COMMIT DROP;

INSERT INTO bad_text_patterns (pattern, reason)
VALUES
  ('www\.|https?://', 'url_or_website'),
  ('[0-9]{3}[- ][0-9]{3}[- ][0-9]{4}', 'phone_number'),
  ('test instrumental|reg\.? ?tm|questions\?', 'testing_trademark_or_contact_text'),
  ('ppm|fluoride content|fluorure|fluorid', 'concentration_or_fluoride_claim'),
  ('pH:|CAS n|lot|batch|mfg|#MFD|EXP\b|best before|L:[0-9]', 'code_lot_ph_or_cas_text'),
  ('agents? de surface|tenside|surfactants|coton|viscose|polyester|nonwoven|materialer|bestandteile|strikker', 'detergent_or_packaging_disclosure'),
  ('organic ingredients|agriculture biologique|certified organic|biologique|natural origin|naturally derived|origine naturelle|made using organic|issued from organic|ingredient of natural origin', 'organic_or_natural_origin_note'),
  ('procter|p\&g|made in|manufactured|import|uvoznik|drogerie|website|consumer|contact', 'manufacturer_or_contact_text'),
  ('do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|contacto con los ojos|en caso de contacto', 'directions_warning_or_safety_text'),
  ('beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que ', 'descriptive_prose'),
  ('^\s*[0-9]+(\.[0-9]+)?\s*%?\s*$', 'bare_number_or_percent');

CREATE TEMP TABLE real_annotation_repairs ON COMMIT DROP AS
SELECT
  pi.id,
  pi.raw_inci_token,
  i.inci_name AS repaired_token
FROM product_ingredients pi
JOIN ingredients i
  ON i.id = pi.ingredient_id
WHERE pi.is_matched
  AND (
    pi.raw_inci_token ~* '&quot'
    OR pi.raw_inci_token ~* '_(amarillo|verde|rojo)='
    OR (
      pi.raw_inci_token ~* '^[[:alpha:] -]+ [0-9]+(\.[0-9]+)?%'
      AND inci_normalize(pi.raw_inci_token) LIKE inci_normalize(i.inci_name) || '%'
    )
    OR pi.raw_inci_token ~* '^(Active Ingredients|Inactive Ingredients|CONTAINS|Ingrédients/Ingredientes|BESTANDTEILE):'
  )
  AND i.inci_name !~* '(www\.|https?://|ppm|fluoride|fluorure|agriculture|biologique|natural origin|made using organic|test instrumental|reg\.? ?tm|questions|contact|do not|avoid|warning|directions?|instructions?|agents? de surface|tenside)'
  AND i.inci_name !~* '^\s*[0-9]+(\.[0-9]+)?\s*%?\s*$';

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'purge_extraneous_v1',
  'matched_real_ingredient_with_label_annotation',
  'rewrite_raw_token_to_canonical_ingredient',
  raw_inci_token,
  count(*)::int,
  jsonb_build_object('repaired_token', max(repaired_token))
FROM real_annotation_repairs
GROUP BY raw_inci_token;

UPDATE product_ingredients pi
SET raw_inci_token = repair.repaired_token
FROM real_annotation_repairs repair
WHERE pi.id = repair.id;

UPDATE product_ingredients pi
SET raw_inci_token = 'CI ' || substring(regexp_replace(pi.raw_inci_token, '\s+', '', 'g') from 3)
WHERE pi.raw_inci_token ~* '^CI[0-9]{5}$';

CREATE TEMP TABLE extraneous_product_rows ON COMMIT DROP AS
SELECT DISTINCT
  pi.id,
  pi.raw_inci_token,
  pi.ingredient_id,
  i.inci_name,
  pattern.reason
FROM product_ingredients pi
LEFT JOIN ingredients i
  ON i.id = pi.ingredient_id
JOIN bad_text_patterns pattern
  ON (
    pi.raw_inci_token ~* pattern.pattern
    OR coalesce(i.inci_name, '') ~* pattern.pattern
  )
WHERE NOT (
    pi.raw_inci_token ~* '^CI ?[0-9]{5}$'
    OR coalesce(i.inci_name, '') ~* '^CI ?[0-9]{5}$'
  )
  AND NOT (
    pi.is_matched
    AND coalesce(i.inci_name, '') !~* '(www\.|https?://|ppm|fluoride|fluorure|agriculture|biologique|natural origin|made using organic|test instrumental|reg\.? ?tm|questions|contact|do not|avoid|warning|directions?|instructions?|agents? de surface|tenside)'
    AND pi.raw_inci_token ~* '^[[:alpha:] -]+ [0-9]+(\.[0-9]+)?%'
    AND inci_normalize(pi.raw_inci_token) LIKE inci_normalize(i.inci_name) || '%'
  );

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'purge_extraneous_v1',
  reason,
  'delete_matched_non_ingredient_product_row',
  raw_inci_token,
  count(*)::int,
  jsonb_build_object('matched_ingredient', max(inci_name))
FROM extraneous_product_rows
GROUP BY reason, raw_inci_token;

DELETE FROM product_ingredients pi
USING extraneous_product_rows bad
WHERE pi.id = bad.id;

CREATE TEMP TABLE bad_aliases ON COMMIT DROP AS
SELECT DISTINCT
  a.id,
  a.alias,
  a.ingredient_id,
  pattern.reason
FROM ingredient_aliases a
JOIN bad_text_patterns pattern
  ON a.alias ~* pattern.pattern
WHERE a.alias !~* '^CI ?[0-9]{5}$';

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'purge_extraneous_v1',
  reason,
  'delete_noise_alias',
  alias,
  count(*)::int,
  NULL
FROM bad_aliases
GROUP BY reason, alias;

DELETE FROM ingredient_aliases a
USING bad_aliases bad
WHERE a.id = bad.id;

CREATE TEMP TABLE bad_ingredients ON COMMIT DROP AS
SELECT DISTINCT
  i.id,
  i.inci_name,
  pattern.reason
FROM ingredients i
JOIN bad_text_patterns pattern
  ON i.inci_name ~* pattern.pattern
WHERE i.inci_name !~* '^CI ?[0-9]{5}$'
  AND NOT EXISTS (
    SELECT 1
    FROM product_ingredients pi
    WHERE pi.ingredient_id = i.id
  );

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'purge_extraneous_v1',
  reason,
  'delete_unreferenced_bogus_ingredient',
  inci_name,
  count(*)::int,
  NULL
FROM bad_ingredients
GROUP BY reason, inci_name;

DELETE FROM ingredient_aliases a
USING bad_ingredients bad
WHERE a.ingredient_id = bad.id;

DELETE FROM ingredients i
USING bad_ingredients bad
WHERE i.id = bad.id;

CREATE TEMP TABLE affected_products ON COMMIT DROP AS
WITH numbered AS (
  SELECT
    product_id,
    position,
    row_number() OVER (PARTITION BY product_id ORDER BY position) AS expected
  FROM product_ingredients
)
SELECT DISTINCT product_id
FROM numbered
WHERE position <> expected;

CREATE TEMP TABLE renumber_products ON COMMIT DROP AS
SELECT
  pi.id,
  row_number() OVER (PARTITION BY pi.product_id ORDER BY pi.position, pi.id)::int AS new_position
FROM product_ingredients pi
JOIN affected_products affected
  ON affected.product_id = pi.product_id;

UPDATE product_ingredients pi
SET position = -renumber.new_position
FROM renumber_products renumber
WHERE pi.id = renumber.id;

UPDATE product_ingredients
SET position = -position
WHERE position < 0;


UPDATE products
SET ingredient_fingerprint = NULL;

WITH product_fingerprints AS (
  SELECT
    product_id,
    md5(string_agg(upper(trim(raw_inci_token)), '|' ORDER BY position)) AS fingerprint
  FROM product_ingredients
  WHERE raw_inci_token IS NOT NULL
    AND trim(raw_inci_token) <> ''
  GROUP BY product_id
),
unique_fingerprints AS (
  SELECT
    product_id,
    fingerprint,
    count(*) OVER (PARTITION BY fingerprint) AS duplicate_count
  FROM product_fingerprints
)
UPDATE products p
SET ingredient_fingerprint = CASE
    WHEN u.duplicate_count = 1 THEN u.fingerprint
    ELSE NULL
  END
FROM unique_fingerprints u
WHERE p.id = u.product_id;

COMMIT;
