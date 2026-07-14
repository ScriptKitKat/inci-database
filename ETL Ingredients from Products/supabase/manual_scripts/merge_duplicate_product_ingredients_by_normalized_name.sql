BEGIN;

SET LOCAL statement_timeout = '15min';

CREATE TEMP TABLE product_ingredient_normalized_groups ON COMMIT DROP AS
WITH keyed AS (
  SELECT
    pi.id,
    pi.product_id,
    pi.position,
    pi.raw_inci_token,
    pi.ingredient_id,
    pi.is_matched,
    coalesce(i.normalized_name, inci_normalize(pi.raw_inci_token)) AS normalized_ingredient_name
  FROM product_ingredients pi
  LEFT JOIN ingredients i
    ON i.id = pi.ingredient_id
  WHERE btrim(coalesce(i.normalized_name, inci_normalize(pi.raw_inci_token), '')) <> ''
),
duplicate_groups AS (
  SELECT
    product_id,
    normalized_ingredient_name,
    min(position) AS first_position,
    count(*) AS row_count
  FROM keyed
  GROUP BY product_id, normalized_ingredient_name
  HAVING count(*) > 1
),
ranked AS (
  SELECT
    keyed.*,
    duplicate_groups.first_position,
    row_number() OVER (
      PARTITION BY keyed.product_id, keyed.normalized_ingredient_name
      ORDER BY
        keyed.is_matched DESC,
        (keyed.ingredient_id IS NOT NULL) DESC,
        keyed.position,
        keyed.id
    ) AS keep_rank
  FROM keyed
  JOIN duplicate_groups
    ON duplicate_groups.product_id = keyed.product_id
   AND duplicate_groups.normalized_ingredient_name = keyed.normalized_ingredient_name
)
SELECT *
FROM ranked;

CREATE TABLE IF NOT EXISTS product_ingredient_merge_backup_20260630_normalized_name (
  backed_up_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  product_id UUID NOT NULL,
  normalized_ingredient_name TEXT NOT NULL,
  kept_row JSONB NOT NULL,
  deleted_rows JSONB NOT NULL
);

INSERT INTO product_ingredient_merge_backup_20260630_normalized_name (
  product_id,
  normalized_ingredient_name,
  kept_row,
  deleted_rows
)
SELECT
  kept.product_id,
  kept.normalized_ingredient_name,
  to_jsonb(kept) AS kept_row,
  jsonb_agg(to_jsonb(deleted) ORDER BY deleted.position, deleted.id) AS deleted_rows
FROM product_ingredient_normalized_groups kept
JOIN product_ingredient_normalized_groups deleted
  ON deleted.product_id = kept.product_id
 AND deleted.normalized_ingredient_name = kept.normalized_ingredient_name
 AND deleted.keep_rank > 1
WHERE kept.keep_rank = 1
GROUP BY kept.product_id, kept.normalized_ingredient_name, kept;

CREATE TEMP TABLE rows_to_delete ON COMMIT DROP AS
SELECT id
FROM product_ingredient_normalized_groups
WHERE keep_rank > 1;

CREATE TEMP TABLE keepers_to_reposition ON COMMIT DROP AS
SELECT id, first_position
FROM product_ingredient_normalized_groups
WHERE keep_rank = 1
  AND position <> first_position;

CREATE TEMP TABLE affected_products ON COMMIT DROP AS
SELECT DISTINCT product_id
FROM product_ingredient_normalized_groups;

DELETE FROM product_ingredients pi
USING rows_to_delete deleted
WHERE pi.id = deleted.id;

UPDATE product_ingredients pi
SET position = keepers.first_position
FROM keepers_to_reposition keepers
WHERE pi.id = keepers.id;

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
