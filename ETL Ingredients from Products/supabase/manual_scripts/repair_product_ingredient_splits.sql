BEGIN;

CREATE TEMP TABLE product_ingredient_pair_repairs ON COMMIT DROP AS
WITH matched_terms AS (
  SELECT DISTINCT ON (term)
    term,
    ingredient_id
  FROM (
    SELECT normalized_name AS term, id AS ingredient_id, 0 AS priority
    FROM ingredients
    WHERE normalized_name IS NOT NULL
    UNION ALL
    SELECT normalized_alias AS term, ingredient_id, 1 AS priority
    FROM ingredient_aliases
    WHERE normalized_alias IS NOT NULL
  ) terms
  ORDER BY term, priority
),
repair_suffixes(term) AS (
  VALUES
    ('butter'),
    ('extract'),
    ('ferment'),
    ('juice'),
    ('oil'),
    ('powder'),
    ('wax'),
    ('water'),
    ('bark extract'),
    ('flower extract'),
    ('fruit extract'),
    ('kernel oil'),
    ('leaf extract'),
    ('leaf juice'),
    ('peel extract'),
    ('peel oil'),
    ('root extract'),
    ('seed butter'),
    ('seed extract'),
    ('seed oil'),
    ('seed powder')
),
base_candidates AS (
  SELECT
    pi1.id AS keep_id,
    pi2.id AS delete_id,
    pi1.product_id,
    pi1.position AS keep_position,
    pi2.position AS delete_position,
    pi1.raw_inci_token || ' ' || pi2.raw_inci_token AS merged_token,
    mt.ingredient_id AS merged_ingredient_id,
    strpos(inci_normalize(pi2.raw_inci_token), ' ') > 0 AS suffix_has_space
  FROM product_ingredients pi1
  JOIN product_ingredients pi2
    ON pi2.product_id = pi1.product_id
   AND pi2.position = pi1.position + 1
  JOIN repair_suffixes suffix
    ON suffix.term = inci_normalize(pi2.raw_inci_token)
  LEFT JOIN matched_terms mt
    ON mt.term = inci_normalize(pi1.raw_inci_token || ' ' || pi2.raw_inci_token)
  WHERE
    mt.ingredient_id IS NOT NULL
    OR strpos(inci_normalize(pi2.raw_inci_token), ' ') > 0
    OR NOT EXISTS (
      SELECT 1
      FROM matched_terms st
      WHERE st.term = inci_normalize(pi1.raw_inci_token)
    )
    OR split_part(
      inci_normalize(pi1.raw_inci_token),
      ' ',
      array_length(string_to_array(inci_normalize(pi1.raw_inci_token), ' '), 1)
    ) IN ('bark', 'flower', 'fruit', 'kernel', 'leaf', 'root', 'seed', 'stem')
)
SELECT *
FROM base_candidates candidate
WHERE NOT EXISTS (
    SELECT 1
    FROM base_candidates other
    WHERE other.keep_id = candidate.delete_id
  )
  AND NOT EXISTS (
    SELECT 1
    FROM base_candidates other
    WHERE other.delete_id = candidate.keep_id
  );

CREATE TEMP TABLE product_ingredient_noise_deletions ON COMMIT DROP AS
SELECT
  id AS delete_id,
  product_id,
  position AS delete_position
FROM product_ingredients
WHERE raw_inci_token ~ '^[A-Za-z]$'
  AND id NOT IN (SELECT keep_id FROM product_ingredient_pair_repairs)
  AND id NOT IN (SELECT delete_id FROM product_ingredient_pair_repairs);

CREATE TEMP TABLE product_ingredient_deleted_positions ON COMMIT DROP AS
SELECT product_id, delete_position
FROM product_ingredient_pair_repairs
UNION ALL
SELECT product_id, delete_position
FROM product_ingredient_noise_deletions;

UPDATE product_ingredients pi
SET raw_inci_token = repair.merged_token,
    ingredient_id = repair.merged_ingredient_id,
    is_matched = repair.merged_ingredient_id IS NOT NULL
FROM product_ingredient_pair_repairs repair
WHERE pi.id = repair.keep_id;

DELETE FROM product_ingredients pi
USING product_ingredient_pair_repairs repair
WHERE pi.id = repair.delete_id;

DELETE FROM product_ingredients pi
USING product_ingredient_noise_deletions noise
WHERE pi.id = noise.delete_id;

UPDATE product_ingredients pi
SET position = -position
WHERE EXISTS (
  SELECT 1
  FROM product_ingredient_deleted_positions deleted
  WHERE deleted.product_id = pi.product_id
);

UPDATE product_ingredients pi
SET position = abs(position) - (
  SELECT count(*)
  FROM product_ingredient_deleted_positions deleted
  WHERE deleted.product_id = pi.product_id
    AND deleted.delete_position < abs(pi.position)
)
WHERE position < 0;

COMMIT;
