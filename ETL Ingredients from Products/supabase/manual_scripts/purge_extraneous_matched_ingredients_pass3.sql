BEGIN;

SET LOCAL statement_timeout = '10min';

INSERT INTO ingredients (inci_name, slug, function_tags)
VALUES
  ('SODIUM FLUORIDE', 'sodium-fluoride', ARRAY['oral-care'])
ON CONFLICT (inci_name) DO NOTHING;

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

CREATE TEMP TABLE manual_repairs (
  source_term TEXT PRIMARY KEY,
  target_term TEXT NOT NULL
) ON COMMIT DROP;

INSERT INTO manual_repairs (source_term, target_term)
VALUES
  ('Sodium flouride 0.243%', 'SODIUM FLUORIDE'),
  ('Sodium monoflourophosphate 0.76%', 'SODIUM MONOFLUOROPHOSPHATE'),
  ('Sodium Monofluorophosphate 0.76%', 'SODIUM MONOFLUOROPHOSPHATE'),
  ('10% p/p de Monofluorophosphate de Sodium', 'SODIUM MONOFLUOROPHOSPHATE'),
  ('Contains Sodium Monofluorophosphate 0. 76% w/w', 'SODIUM MONOFLUOROPHOSPHATE'),
  ('BHT. Contains Sodium Monofluorophosphate 0.76% w/w', 'SODIUM MONOFLUOROPHOSPHATE'),
  ('BHT. Contains Sodium Monofluorophosphate 1.1% w/w', 'SODIUM MONOFLUOROPHOSPHATE'),
  ('Butyl methoxydibenzoylmethane 5%', 'Avobenzone'),
  ('Octyl salicylate 5%', 'Octisalate'),
  ('Glycerol 85%', 'GLYCERIN'),
  ('C13-14 Isoparafina_amarillo=', 'C13-14 ISOPARAFFIN'),
  ('Caprylyl Glycol_verde=', 'CAPRYLYL GLYCOL'),
  ('Extracto de Centella Asiática_verde=', 'CENTELLA ASIATICA EXTRACT'),
  ('Extracto de hoja de Camellia Sinensis_verde=', 'CAMELLIA SINENSIS LEAF EXTRACT'),
  ('Glutamato de estearoil disódico_amarillo=', 'DISODIUM STEAROYL GLUTAMATE'),
  ('100% Sheabutter', 'SHEA BUTTER'),
  ('100% Opuntia Ficus-Indica Seed Oil', 'OPUNTIA FICUS-INDICA SEED OIL'),
  ('100% Moringa Seed Kernel Oil', 'MORINGA SEED OIL'),
  ('Carbamide Peroxide', 'CARBAMIDE PEROXIDE');

CREATE TEMP TABLE manual_product_repairs ON COMMIT DROP AS
SELECT
  pi.id,
  mt.ingredient_id,
  mt.canonical_name
FROM product_ingredients pi
JOIN manual_repairs mr
  ON inci_normalize(pi.raw_inci_token) = inci_normalize(mr.source_term)
JOIN match_terms mt
  ON mt.term = inci_normalize(mr.target_term)
WHERE pi.is_matched;

UPDATE product_ingredients pi
SET ingredient_id = repair.ingredient_id,
    raw_inci_token = repair.canonical_name,
    is_matched = true
FROM manual_product_repairs repair
WHERE pi.id = repair.id;

CREATE TEMP TABLE concentration_candidates ON COMMIT DROP AS
WITH source_rows AS (
  SELECT
    pi.id,
    regexp_replace(
      regexp_replace(
        regexp_replace(btrim(pi.raw_inci_token), '&quot|&lt|&gt|&amp', '', 'gi'),
        '^[*[:space:]]+|[*.;:[:space:]]+$',
        '',
        'g'
      ),
      '_(amarillo|verde|rojo)=.*$',
      '',
      'i'
    ) AS token
  FROM product_ingredients pi
  WHERE pi.is_matched
    AND pi.raw_inci_token !~* '^CI ?[0-9]{5}$'
    AND (
      pi.raw_inci_token ~* '%|_amarillo=|_verde=|_rojo=|&quot|&lt|&gt|&amp'
      OR pi.raw_inci_token ~* '^[*[:space:]]+|[*.;:[:space:]]+$'
    )
),
candidates AS (
  SELECT id, token AS candidate, 0 AS priority FROM source_rows
  UNION ALL
  SELECT id, regexp_replace(token, '^[0-9]+([.,][0-9]+)?[[:space:]]*%[[:space:]]*(pure[[:space:]]+)?', '', 'i'), 1 FROM source_rows
  UNION ALL
  SELECT id, regexp_replace(token, '[[:space:]]*[-–]?[[:space:]]*[0-9]+([.,][0-9]+)?[[:space:]]*%.*$', '', 'i'), 2 FROM source_rows
  UNION ALL
  SELECT id, regexp_replace(regexp_replace(token, '^Contains[[:space:]]+', '', 'i'), '[[:space:]]+[0-9]+([.,][0-9]+)?[[:space:]]*%.*$', '', 'i'), 3 FROM source_rows
  UNION ALL
  SELECT id, regexp_replace(token, '[[:space:]]+water$', '', 'i'), 4 FROM source_rows
)
SELECT DISTINCT ON (c.id)
  c.id,
  mt.ingredient_id,
  mt.canonical_name
FROM candidates c
JOIN match_terms mt
  ON mt.term = inci_normalize(btrim(c.candidate))
WHERE length(btrim(c.candidate)) > 2
ORDER BY c.id, c.priority;

UPDATE product_ingredients pi
SET ingredient_id = repair.ingredient_id,
    raw_inci_token = repair.canonical_name,
    is_matched = true
FROM concentration_candidates repair
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
    OR coalesce(i.inci_name, '') ~* 'CITRUS .* PEEL OIL EXPRESSED$'
  )
  AND (
    pi.ingredient_id IS NULL
    OR pi.raw_inci_token ~* 'www\.|https?://|[0-9]{3}[- ][0-9]{3}[- ][0-9]{4}'
    OR pi.raw_inci_token ~* 'ppm|fluoride content|fluorure|fluorid|pH:|CAS n|lot|batch|mfg|#MFD|EXP\b|L:[0-9]'
    OR pi.raw_inci_token ~* 'agriculture biologique|certified organic|biologique|natural origin|naturally derived|made using organic|issued from organic|ingredient of natural origin|organic ingredients'
    OR pi.raw_inci_token ~* 'agents? de surface|tenside|surfactants|coton|viscose|polyester|polyamide|nonwoven|materialer|bestandteile|strikker|ouate|cellulose cert'
    OR pi.raw_inci_token ~* 'procter|p\&g|made in|manufactured|fabricado|distribuido|exportado|import|uvoznik|drogerie|consumer|contacto|contact|do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|en caso de contacto'
    OR pi.raw_inci_token ~* 'beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que |equivalent to|excipients|sweetener|preservatives|expected protection|exposition solaire|correcteur'
    OR pi.raw_inci_token ~* '%|=|&quot|&lt|&gt'
    OR pi.raw_inci_token ~* '^\s*(EXPRESSED|EXPERIMENTA|EXPERT TOUCH|EXPLORE THE|EXPONER|EXPORTADO|EXPRACT|EXPRI[[:space:]]|FOR/Y GAIN)\b'
    OR length(pi.raw_inci_token) > 140
    OR pi.raw_inci_token ~* '^\s*[0-9]+(\.[0-9]+)?\s*%?\s*$'
    OR coalesce(i.inci_name, '') ~* 'www\.|https?://|[0-9]{3}[- ][0-9]{3}[- ][0-9]{4}'
    OR coalesce(i.inci_name, '') ~* 'ppm|fluoride content|fluorure|fluorid|pH:|CAS n|lot|batch|mfg|#MFD|EXP\b|L:[0-9]'
    OR coalesce(i.inci_name, '') ~* 'agriculture biologique|certified organic|biologique|natural origin|naturally derived|made using organic|issued from organic|ingredient of natural origin|organic ingredients'
    OR coalesce(i.inci_name, '') ~* 'agents? de surface|tenside|surfactants|coton|viscose|polyester|polyamide|nonwoven|materialer|bestandteile|strikker|ouate|cellulose cert'
    OR coalesce(i.inci_name, '') ~* 'procter|p\&g|made in|manufactured|fabricado|distribuido|exportado|import|uvoznik|drogerie|consumer|contacto|contact|do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|en caso de contacto'
    OR coalesce(i.inci_name, '') ~* 'beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que |equivalent to|excipients|sweetener|preservatives|expected protection|exposition solaire|correcteur'
    OR coalesce(i.inci_name, '') ~* '%|=|&quot|&lt|&gt'
    OR coalesce(i.inci_name, '') ~* '^\s*(EXPRESSED|EXPERIMENTA|EXPERT TOUCH|EXPLORE THE|EXPONER|EXPORTADO|EXPRACT|EXPRI[[:space:]]|FOR/Y GAIN)\b'
    OR length(coalesce(i.inci_name, '')) > 140
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
    OR a.alias ~* 'agents? de surface|tenside|surfactants|coton|viscose|polyester|polyamide|nonwoven|materialer|bestandteile|strikker|ouate|cellulose cert'
    OR a.alias ~* 'procter|p\&g|made in|manufactured|fabricado|distribuido|exportado|import|uvoznik|drogerie|consumer|contacto|contact|do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|en caso de contacto'
    OR a.alias ~* 'beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que |equivalent to|excipients|sweetener|preservatives|expected protection|exposition solaire|correcteur'
    OR a.alias ~* '%|=|&quot|&lt|&gt'
    OR a.alias ~* '^\s*(EXPRESSED|EXPERIMENTA|EXPERT TOUCH|EXPLORE THE|EXPONER|EXPORTADO|EXPRACT|EXPRI[[:space:]]|FOR/Y GAIN)\b'
  );

DELETE FROM ingredient_aliases a
USING bad_aliases bad
WHERE a.id = bad.id;

CREATE TEMP TABLE bad_ingredients ON COMMIT DROP AS
SELECT DISTINCT i.id
FROM ingredients i
WHERE i.inci_name !~* '^CI ?[0-9]{5}$'
  AND i.inci_name !~* 'CITRUS .* PEEL OIL EXPRESSED$'
  AND NOT EXISTS (
    SELECT 1
    FROM product_ingredients pi
    WHERE pi.ingredient_id = i.id
  )
  AND (
    i.inci_name ~* 'www\.|https?://|[0-9]{3}[- ][0-9]{3}[- ][0-9]{4}'
    OR i.inci_name ~* 'ppm|fluoride content|fluorure|fluorid|pH:|CAS n|lot|batch|mfg|#MFD|EXP\b|L:[0-9]'
    OR i.inci_name ~* 'agriculture biologique|certified organic|biologique|natural origin|naturally derived|made using organic|issued from organic|ingredient of natural origin|organic ingredients'
    OR i.inci_name ~* 'agents? de surface|tenside|surfactants|coton|viscose|polyester|polyamide|nonwoven|materialer|bestandteile|strikker|ouate|cellulose cert'
    OR i.inci_name ~* 'procter|p\&g|made in|manufactured|fabricado|distribuido|exportado|import|uvoznik|drogerie|consumer|contacto|contact|do not|avoid|warning|caution|directions?|instructions?|apply|rinse|massage|external use|children|poison|store at|enjuague|mantengase|en caso de contacto'
    OR i.inci_name ~* 'beneficios|consideraciones|seguro|producto|actúa|ayuda|emoliente|filtro solar|para | que |equivalent to|excipients|sweetener|preservatives|expected protection|exposition solaire|correcteur'
    OR i.inci_name ~* '%|=|&quot|&lt|&gt'
    OR i.inci_name ~* '^\s*(EXPRESSED|EXPERIMENTA|EXPERT TOUCH|EXPLORE THE|EXPONER|EXPORTADO|EXPRACT|EXPRI[[:space:]]|FOR/Y GAIN)\b'
    OR length(i.inci_name) > 140
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
