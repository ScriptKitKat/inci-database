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

CREATE TEMP TABLE pass3_ingredient_seed (
  inci_name TEXT PRIMARY KEY,
  function_tag TEXT NOT NULL
) ON COMMIT DROP;

INSERT INTO pass3_ingredient_seed (inci_name, function_tag)
VALUES
  ('Octisalate', 'uv filter'),
  ('Homosalate', 'uv filter'),
  ('Avobenzone', 'uv filter'),
  ('Octocrylene', 'uv filter'),
  ('Stannous Fluoride', 'oral care'),
  ('Sodium Fluoride', 'oral care'),
  ('Sodium Bicarbonate', 'buffering'),
  ('Hydrated Silica', 'abrasive'),
  ('Butane', 'propellant'),
  ('Tin Oxide', 'colorant'),
  ('Isononyl Isononanoate', 'emollient'),
  ('Disteardimonium Hectorite', 'texture'),
  ('Palmitic Acid', 'emollient');

INSERT INTO ingredients (inci_name, slug, function_tags)
SELECT
  seed.inci_name,
  regexp_replace(
    lower(regexp_replace(seed.inci_name, '[^a-zA-Z0-9]+', '-', 'g')),
    '(^-|-$)',
    '',
    'g'
  ) || '-' || left(md5(seed.inci_name), 6),
  ARRAY[seed.function_tag]
FROM pass3_ingredient_seed seed
WHERE NOT EXISTS (
  SELECT 1
  FROM ingredients existing
  WHERE existing.normalized_name = inci_normalize(seed.inci_name)
);

CREATE TEMP TABLE pass3_alias_seed (
  canonical_name TEXT NOT NULL,
  alias TEXT NOT NULL,
  alias_type alias_type NOT NULL DEFAULT 'synonym',
  language TEXT NOT NULL DEFAULT 'en'
) ON COMMIT DROP;

INSERT INTO pass3_alias_seed (canonical_name, alias, alias_type, language)
VALUES
  ('Octisalate', 'Octisalate 5%', 'synonym', 'en'),
  ('Octisalate', 'Octisalate 4.5%', 'synonym', 'en'),
  ('Octisalate', 'Octyl salicylate 5%', 'synonym', 'en'),
  ('Homosalate', 'Homosalate 10%', 'synonym', 'en'),
  ('Homosalate', 'Homosalate 5.5%', 'synonym', 'en'),
  ('Avobenzone', 'Avobenzone 3%', 'synonym', 'en'),
  ('Avobenzone', 'Active Ingredients: Avobenzone 3%', 'synonym', 'en'),
  ('Avobenzone', 'Butyl methoxydibenzoylmethane 5%', 'synonym', 'en'),
  ('Octocrylene', 'octocrylene 4%', 'synonym', 'en'),
  ('Octocrylene', 'Octocrylene 2.7%', 'synonym', 'en'),
  ('Octocrylene', 'Octocrylene 7%', 'synonym', 'en'),
  ('Hydrated Silica', 'hydrated silica [nano]', 'synonym', 'en'),
  ('Ascorbic Acid', 'CONTAINS:Ascorbic Acid', 'synonym', 'en'),
  ('AQUA', 'Inactive Ingredients: Aqua/Water/Eau', 'synonym', 'en'),
  ('AQUA', 'BESTANDTEILE: Wasser', 'translation', 'de'),
  ('Sodium Bicarbonate', 'Ingrédients/Ingredientes: Sodium Bicarbonate', 'synonym', 'en'),
  ('Butane', 'Inactive Ingredients: Butane', 'synonym', 'en'),
  ('Stannous Fluoride', 'Stannous fluoride 0.454%', 'synonym', 'en'),
  ('Alcohol', 'Alcohol&quot', 'typo', 'en'),
  ('Alcohol', 'ALCOHOL&quot', 'typo', 'en'),
  ('Geraniol', 'Geraniol&quot', 'typo', 'en'),
  ('Geraniol', 'GERANIOL&quot', 'typo', 'en'),
  ('Limonene', 'Limonene&quot', 'typo', 'en'),
  ('Limonene', 'LIMONENE&quot', 'typo', 'en'),
  ('Limonene', 'LIMONENE &quot', 'typo', 'en'),
  ('Glycerin', 'GLYCERIN&quot', 'typo', 'en'),
  ('Linalool', 'LINALOOL&quot', 'typo', 'en'),
  ('Linalool', 'LINALOOL &quot', 'typo', 'en'),
  ('Betaine', 'BETAINE &quot', 'typo', 'en'),
  ('Cera Alba', 'Cera Alba&quot', 'typo', 'en'),
  ('Phenoxyethanol', 'Fenoxietanol_rojo=', 'translation', 'es'),
  ('Butylene Glycol', 'Glicol de butileno_amarillo=', 'translation', 'es'),
  ('Silica', 'Sílice_amarillo=', 'translation', 'es'),
  ('Dimethicone', 'Dimeticona_amarillo=', 'translation', 'es'),
  ('Tocopherol', 'Tocoferol_verde=', 'translation', 'es'),
  ('Hydrogenated Polyisobutene', 'Poliisobuteno hidrogenado_amarillo=', 'translation', 'es'),
  ('Tin Oxide', 'Óxido de estaño_amarillo=', 'translation', 'es'),
  ('Isononyl Isononanoate', 'Isononil isononanoato_amarillo=', 'translation', 'es'),
  ('Disteardimonium Hectorite', 'Hectorita de disteardimonio_amarillo=', 'translation', 'es'),
  ('Ethylhexylglycerin', 'Etilhexilglicerina_amarillo=', 'translation', 'es'),
  ('Palmitic Acid', 'Ácido palmítico_amarillo=', 'translation', 'es');

INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
SELECT
  ingredient.id,
  alias_seed.alias,
  alias_seed.alias_type,
  alias_seed.language,
  'manual'
FROM pass3_alias_seed alias_seed
JOIN LATERAL (
  SELECT id
  FROM ingredients
  WHERE normalized_name = inci_normalize(alias_seed.canonical_name)
  ORDER BY (inci_name = alias_seed.canonical_name) DESC, created_at ASC
  LIMIT 1
) ingredient ON true
WHERE btrim(alias_seed.alias) <> ''
ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

CREATE TEMP TABLE match_terms ON COMMIT DROP AS
SELECT DISTINCT ON (term)
  term,
  ingredient_id
FROM (
  SELECT normalized_name AS term, id AS ingredient_id, 0 AS priority
  FROM ingredients
  WHERE btrim(coalesce(normalized_name, '')) <> ''
  UNION ALL
  SELECT
    normalized_alias AS term,
    ingredient_id,
    CASE WHEN source = 'manual' THEN 1 ELSE 2 END AS priority
  FROM ingredient_aliases
  WHERE btrim(coalesce(normalized_alias, '')) <> ''
) terms
ORDER BY term, priority;

UPDATE product_ingredients pi
SET ingredient_id = terms.ingredient_id,
    is_matched = true
FROM match_terms terms
WHERE NOT pi.is_matched
  AND terms.term = inci_normalize(pi.raw_inci_token);

CREATE TEMP TABLE pass3_noise_tokens ON COMMIT DROP AS
SELECT
  raw_inci_token,
  count(*)::int AS rows,
  CASE
    WHEN raw_inci_token ~ '[%=_]' THEN 'percentage_or_annotation_not_inci'
    WHEN length(raw_inci_token) > 140 THEN 'long_unsplit_prose_or_ingredient_run'
    WHEN raw_inci_token ~* '&quot|&lt|&gt' THEN 'html_residue'
    ELSE 'regulatory_or_marketing_disclosure'
  END AS reason
FROM product_ingredients
WHERE NOT is_matched
  AND (
    raw_inci_token ~ '[%=_]'
    OR raw_inci_token ~* '&quot|&lt|&gt'
    OR length(raw_inci_token) > 140
    OR raw_inci_token ~* 'ppm|agents? de surface|tenside|coton|procter|p\&g|made in|contient|contains:|inactive ingredients|active ingredients|ingredientes:|ingrédients|d.origin|biologique|agriculture|puede|actúa|ayuda|emoliente|filtro solar|que |para |with a formula|insert one|seek medical|do not|avoid|skin|viscose|fluoride|fluorure|c12-15 pareth|benzisothiazolinone|sodium laureth sulfate\.|octylisothiazolinone|materialer|bestandteile|strikker|drogerie|import|uvoznik|excipients|preservatives|sweetener|alimenticia|sauerstoffbasis|nonwoven'
  )
GROUP BY raw_inci_token;

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'reduce_unmatched_v3',
  reason,
  'delete_non_inci_residue',
  raw_inci_token,
  rows,
  NULL
FROM pass3_noise_tokens;

DELETE FROM product_ingredients pi
USING pass3_noise_tokens noise
WHERE NOT pi.is_matched
  AND pi.raw_inci_token = noise.raw_inci_token;

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

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'reduce_unmatched_v3',
  'run_end_unmatched_count',
  'measure',
  NULL,
  count(*) FILTER (WHERE NOT is_matched)::int,
  jsonb_build_object(
    'distinct_unmatched_tokens',
    count(DISTINCT raw_inci_token) FILTER (WHERE NOT is_matched)
  )
FROM product_ingredients;

COMMIT;
