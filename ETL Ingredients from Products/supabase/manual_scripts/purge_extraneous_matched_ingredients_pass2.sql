BEGIN;

SET LOCAL statement_timeout = '10min';

CREATE TEMP TABLE match_terms ON COMMIT DROP AS
SELECT DISTINCT ON (term)
  term,
  ingredient_id,
  canonical_name
FROM (
  SELECT normalized_name AS term, id AS ingredient_id, inci_name AS canonical_name, 0 AS priority
  FROM ingredients
  WHERE btrim(coalesce(normalized_name, '')) <> ''
  UNION ALL
  SELECT
    normalized_alias AS term,
    ingredient_id,
    (SELECT inci_name FROM ingredients i WHERE i.id = ingredient_aliases.ingredient_id) AS canonical_name,
    CASE WHEN source = 'manual' THEN 1 ELSE 2 END AS priority
  FROM ingredient_aliases
  WHERE btrim(coalesce(normalized_alias, '')) <> ''
) terms
ORDER BY term, priority;

UPDATE product_ingredients pi
SET raw_inci_token = i.inci_name
FROM ingredients i
WHERE pi.ingredient_id = i.id
  AND i.inci_name ~* '^CI ?[0-9]{5}$'
  AND pi.raw_inci_token ~* '^[0-9]{5}$';

CREATE TEMP TABLE html_entity_repairs ON COMMIT DROP AS
SELECT
  pi.id,
  pi.ingredient_id AS old_ingredient_id,
  mt.ingredient_id AS new_ingredient_id,
  mt.canonical_name AS repaired_token
FROM product_ingredients pi
JOIN match_terms mt
  ON mt.term = inci_normalize(
    btrim(
      regexp_replace(
        regexp_replace(pi.raw_inci_token, '&quot|&lt|&gt|&amp', '', 'gi'),
        '[.;:]+$',
        '',
        'g'
      )
    )
  )
WHERE pi.is_matched
  AND pi.raw_inci_token ~* '&quot|&lt|&gt|&amp';

UPDATE product_ingredients pi
SET ingredient_id = repair.new_ingredient_id,
    raw_inci_token = repair.repaired_token,
    is_matched = true
FROM html_entity_repairs repair
WHERE pi.id = repair.id;

CREATE TEMP TABLE purge_rows ON COMMIT DROP AS
SELECT DISTINCT
  pi.id,
  pi.raw_inci_token,
  pi.ingredient_id,
  i.inci_name
FROM product_ingredients pi
LEFT JOIN ingredients i
  ON i.id = pi.ingredient_id
WHERE pi.is_matched
  AND NOT (
    pi.raw_inci_token ~* '^CI ?[0-9]{5}$'
    OR coalesce(i.inci_name, '') ~* '^CI ?[0-9]{5}$'
  )
  AND (
    pi.raw_inci_token ~* 'www\.|https?://|[0-9]{3}[- ][0-9]{3}[- ][0-9]{4}'
    OR pi.raw_inci_token ~* 'ppm|fluoride content|fluorure|fluorid|pH:|CAS n|lot|batch|mfg|#MFD|EXP\b|L:[0-9]'
    OR pi.raw_inci_token ~* 'agriculture biologique|certified organic|biologique|natural origin|naturally derived|made using organic|issued from organic|ingredient of natural origin|organic ingredients'
    OR pi.raw_inci_token ~* 'agents? de surface|tenside|surfactants|coton|viscose|polyester|nonwoven|materialer|bestandteile|strikker|ouate|cellulose cert'
    OR pi.raw_inci_token ~* 'procter|p\&g|made in|manufactured|import|uvoznik|drogerie|consumer|contacto|contact|do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|en caso de contacto'
    OR pi.raw_inci_token ~* 'beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que |equivalent to|excipients|sweetener|preservatives'
    OR pi.raw_inci_token ~* '^\s*[0-9]+(\.[0-9]+)?\s*%?\s*$'
    OR (
      pi.raw_inci_token ~* '&quot|&lt|&gt|&amp'
      AND NOT EXISTS (SELECT 1 FROM html_entity_repairs r WHERE r.id = pi.id)
    )
    OR coalesce(i.inci_name, '') ~* 'www\.|https?://|ppm|agriculture biologique|certified organic|biologique|natural origin|made using organic|test instrumental|reg\.? ?tm|questions|agents? de surface|tenside|contacto|contact|do not|avoid|warning|directions?|instructions?|^\s*[0-9]+(\.[0-9]+)?\s*%?\s*$'
  );

DELETE FROM product_ingredients pi
USING purge_rows bad
WHERE pi.id = bad.id;

CREATE TEMP TABLE bad_aliases ON COMMIT DROP AS
SELECT DISTINCT a.id
FROM ingredient_aliases a
WHERE a.alias !~* '^CI ?[0-9]{5}$'
  AND (
    a.alias ~* 'www\.|https?://|[0-9]{3}[- ][0-9]{3}[- ][0-9]{4}'
    OR a.alias ~* 'ppm|fluoride content|fluorure|fluorid|pH:|CAS n|lot|batch|mfg|#MFD|EXP\b|L:[0-9]'
    OR a.alias ~* 'agriculture biologique|certified organic|biologique|natural origin|naturally derived|made using organic|issued from organic|ingredient of natural origin|organic ingredients'
    OR a.alias ~* 'agents? de surface|tenside|surfactants|coton|viscose|polyester|nonwoven|materialer|bestandteile|strikker|ouate|cellulose cert'
    OR a.alias ~* 'procter|p\&g|made in|manufactured|import|uvoznik|drogerie|consumer|contacto|contact|do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|en caso de contacto'
    OR a.alias ~* 'beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que |equivalent to|excipients|sweetener|preservatives'
    OR a.alias ~* '^\s*[0-9]+(\.[0-9]+)?\s*%?\s*$'
  );

DELETE FROM ingredient_aliases a
USING bad_aliases bad
WHERE a.id = bad.id;

CREATE TEMP TABLE bad_ingredients ON COMMIT DROP AS
SELECT DISTINCT i.id
FROM ingredients i
WHERE i.inci_name !~* '^CI ?[0-9]{5}$'
  AND NOT EXISTS (
    SELECT 1
    FROM product_ingredients pi
    WHERE pi.ingredient_id = i.id
  )
  AND (
    i.inci_name ~* 'www\.|https?://|[0-9]{3}[- ][0-9]{3}[- ][0-9]{4}'
    OR i.inci_name ~* 'ppm|fluoride content|fluorure|fluorid|pH:|CAS n|lot|batch|mfg|#MFD|EXP\b|L:[0-9]'
    OR i.inci_name ~* 'agriculture biologique|certified organic|biologique|natural origin|naturally derived|made using organic|issued from organic|ingredient of natural origin|organic ingredients'
    OR i.inci_name ~* 'agents? de surface|tenside|surfactants|coton|viscose|polyester|nonwoven|materialer|bestandteile|strikker|ouate|cellulose cert'
    OR i.inci_name ~* 'procter|p\&g|made in|manufactured|import|uvoznik|drogerie|consumer|contacto|contact|do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|en caso de contacto'
    OR i.inci_name ~* 'beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que |equivalent to|excipients|sweetener|preservatives'
    OR i.inci_name ~* '^\s*[0-9]+(\.[0-9]+)?\s*%?\s*$'
    OR i.inci_name ~* '&quot|&lt|&gt|&amp'
  );

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

UPDATE products p
SET status = 'rejected',
    updated_at = now()
WHERE status = 'approved'
  AND NOT EXISTS (
    SELECT 1
    FROM product_ingredients pi
    WHERE pi.product_id = p.id
  );

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
