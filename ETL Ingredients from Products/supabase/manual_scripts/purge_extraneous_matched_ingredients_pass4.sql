BEGIN;

SET LOCAL statement_timeout = '10min';

CREATE TEMP TABLE citrus_repair_target ON COMMIT DROP AS
SELECT id AS ingredient_id, inci_name AS canonical_name
FROM ingredients
WHERE normalized_name = inci_normalize('CITRUS SINENSIS PEEL OIL EXPRESSED')
LIMIT 1;

UPDATE product_ingredients pi
SET ingredient_id = target.ingredient_id,
    raw_inci_token = target.canonical_name,
    is_matched = true
FROM citrus_repair_target target
WHERE pi.is_matched
  AND inci_normalize(pi.raw_inci_token) = inci_normalize('Citrus Sinensis Peel Expressed');

CREATE TEMP TABLE purge_names (name TEXT PRIMARY KEY) ON COMMIT DROP;

INSERT INTO purge_names (name)
VALUES
  ('EXPRESSED'),
  ('behenyl alcohol 90332557 00025 3021tnu2 exp 1'),
  ('EXPERIMENTA'),
  ('EXPERT TOUCH'),
  ('Explore the'),
  ('explore the world of 1x at www'),
  ('explore the world of lux at www'),
  ('EXPONER'),
  ('EXPRACT'),
  ('expri 250ml'),
  ('Nexpert Glycol'),
  ('ore sun exposure'),
  ('Peel Oil Expressed'),
  ('Peusek express 150'),
  ('solares y evitese exponerlo a temperaturas'),
  ('SUPERFICIES EXPONERA'),
  ('Violet Powder Experience Flawless'),
  ('with some variability expected'),
  ('Expeller Pressed High Oleic Sunflower or Safflower Oil');

CREATE TEMP TABLE purge_rows ON COMMIT DROP AS
SELECT DISTINCT pi.id
FROM product_ingredients pi
LEFT JOIN ingredients i
  ON i.id = pi.ingredient_id
WHERE pi.is_matched
  AND (
    EXISTS (
      SELECT 1
      FROM purge_names bad
      WHERE inci_normalize(pi.raw_inci_token) = inci_normalize(bad.name)
    )
    OR EXISTS (
      SELECT 1
      FROM purge_names bad
      WHERE inci_normalize(coalesce(i.inci_name, '')) = inci_normalize(bad.name)
    )
  );

DELETE FROM product_ingredients pi
USING purge_rows bad
WHERE pi.id = bad.id;

CREATE TEMP TABLE bad_ingredients ON COMMIT DROP AS
SELECT DISTINCT i.id
FROM ingredients i
WHERE NOT EXISTS (
    SELECT 1
    FROM product_ingredients pi
    WHERE pi.ingredient_id = i.id
  )
  AND EXISTS (
    SELECT 1
    FROM purge_names bad
    WHERE inci_normalize(i.inci_name) = inci_normalize(bad.name)
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
