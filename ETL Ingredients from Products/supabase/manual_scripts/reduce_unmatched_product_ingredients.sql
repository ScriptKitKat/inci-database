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

CREATE TEMP TABLE cleanup_start_counts ON COMMIT DROP AS
SELECT
  count(*) FILTER (WHERE NOT is_matched)::int AS unmatched_rows,
  count(DISTINCT raw_inci_token) FILTER (WHERE NOT is_matched)::int AS distinct_unmatched_tokens
FROM product_ingredients;

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'reduce_unmatched_v1',
  'run_start_unmatched_count',
  'measure',
  NULL,
  unmatched_rows,
  jsonb_build_object('distinct_unmatched_tokens', distinct_unmatched_tokens)
FROM cleanup_start_counts;

CREATE TEMP TABLE manual_alias_seed (
  canonical_name TEXT NOT NULL,
  alias TEXT NOT NULL,
  alias_type alias_type NOT NULL DEFAULT 'synonym',
  language TEXT NOT NULL DEFAULT 'en'
) ON COMMIT DROP;

INSERT INTO manual_alias_seed (canonical_name, alias, alias_type, language)
VALUES
  ('Parfum', 'PARFUM/FRAGRANCE', 'synonym', 'en'),
  ('Parfum', 'Parfum/Fragrance', 'synonym', 'en'),
  ('Parfum', 'PARFUM/ FRAGRANCE', 'synonym', 'en'),
  ('Parfum', 'Perfume', 'synonym', 'en'),
  ('Parfum', 'PERFUME', 'synonym', 'en'),
  ('Parfum', 'Fragrance', 'synonym', 'en'),
  ('Aroma', 'Flavor', 'synonym', 'en'),
  ('Aroma', 'Flavour', 'synonym', 'en'),
  ('Tocopherol', 'Vitamin E', 'common', 'en'),
  ('Ascorbic Acid', 'Vitamin C', 'common', 'en'),
  ('Alpha-Isomethyl Ionone', 'Alpha-Isomethyl lonone', 'typo', 'en'),
  ('AQUA', 'EAU', 'translation', 'fr'),
  ('AQUA', 'Aqua water', 'synonym', 'en'),
  ('CI 77891', 'Cl 77891', 'typo', 'en'),
  ('CI 42090', 'Cl 42090', 'typo', 'en'),
  ('CI 19140', 'Cl 19140', 'typo', 'en'),
  ('CI 17200', 'Cl 17200', 'typo', 'en'),
  ('CI 16035', 'Cl 16035', 'typo', 'en'),
  ('CI 77491', 'Cl 77491', 'typo', 'en'),
  ('CI 77492', 'Cl 77492', 'typo', 'en'),
  ('CI 77499', 'Cl 77499', 'typo', 'en');

CREATE TEMP TABLE manual_ingredient_seed (
  inci_name TEXT PRIMARY KEY,
  function_tag TEXT NOT NULL
) ON COMMIT DROP;

INSERT INTO manual_ingredient_seed (inci_name, function_tag)
VALUES
  ('Parfum', 'fragrance'),
  ('Aroma', 'flavor'),
  ('Alpha-Isomethyl Ionone', 'fragrance'),
  ('Hydroxyethylcellulose', 'texture'),
  ('Maris Sal', 'skin conditioning'),
  ('Hydrolyzed Keratin', 'hair conditioning'),
  ('PPG-14 Butyl Ether', 'solvent'),
  ('PPG-15 Stearyl Ether', 'emollient'),
  ('Isohexadecane', 'emollient'),
  ('Cetyl Esters', 'emollient'),
  ('Sodium Phytate', 'chelating'),
  ('Synthetic Fluorphlogopite', 'colorant'),
  ('Coconut Acid', 'surfactant'),
  ('Magnesium Aluminum Silicate', 'texture'),
  ('Hydrogenated Lecithin', 'emulsifying'),
  ('Hydrogenated Polyisobutene', 'emollient'),
  ('Sodium Polynaphthalenesulfonate', 'dispersing'),
  ('Bis-Diglyceryl Polyacyladipate-2', 'emollient'),
  ('Sodium Lauroyl Glutamate', 'surfactant'),
  ('Polyisobutene', 'emollient'),
  ('Hydrolyzed Hyaluronic Acid', 'humectant'),
  ('Anhydroxylitol', 'humectant'),
  ('Sorbitan Oleate', 'emulsifying'),
  ('Lanolin Alcohol', 'emollient'),
  ('Phospholipids', 'skin conditioning'),
  ('Sorbitan Caprylate', 'emulsifying'),
  ('Acetyl Cedrene', 'fragrance'),
  ('Silica Silylate', 'texture'),
  ('Ext. Violet 2', 'colorant');

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
FROM manual_ingredient_seed seed
WHERE NOT EXISTS (
  SELECT 1
  FROM ingredients existing
  WHERE existing.normalized_name = inci_normalize(seed.inci_name)
);

INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
SELECT
  ingredient.id,
  alias_seed.alias,
  alias_seed.alias_type,
  alias_seed.language,
  'manual'
FROM manual_alias_seed alias_seed
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

CREATE TEMP TABLE section_prefix_repairs ON COMMIT DROP AS
SELECT
  pi.id,
  pi.raw_inci_token,
  CASE
    WHEN pi.raw_inci_token ~* ':\s*(aqua|water|eau)(\s+water)?\s*$' THEN 'AQUA'
    WHEN pi.raw_inci_token ~* '^\s*(ingredients?|ngredients?|ingredientes)\s+(aqua|water|eau)\s*$' THEN 'AQUA'
    ELSE btrim(regexp_replace(pi.raw_inci_token, '^.*:\s*', '', 'g'))
  END AS repaired_token
FROM product_ingredients pi
WHERE NOT pi.is_matched
  AND (
    pi.raw_inci_token ~* ':\s*(aqua|water|eau)(\s+water)?\s*$'
    OR pi.raw_inci_token ~* '^\s*(ingredients?|ngredients?|ingredientes)\s+(aqua|water|eau)\s*$'
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
  'reduce_unmatched_v1',
  'section_prefix_contains_real_ingredient',
  'rewrite_raw_token_and_match',
  raw_inci_token,
  count(*)::int,
  jsonb_build_object('repaired_token', max(repaired_token))
FROM section_prefix_repairs
GROUP BY raw_inci_token;

UPDATE product_ingredients pi
SET raw_inci_token = repair.repaired_token,
    ingredient_id = terms.ingredient_id,
    is_matched = true
FROM section_prefix_repairs repair
JOIN match_terms terms
  ON terms.term = inci_normalize(repair.repaired_token)
WHERE pi.id = repair.id;

UPDATE product_ingredients pi
SET ingredient_id = terms.ingredient_id,
    is_matched = true
FROM match_terms terms
WHERE NOT pi.is_matched
  AND terms.term = inci_normalize(pi.raw_inci_token);

CREATE TEMP TABLE likely_real_tokens ON COMMIT DROP AS
WITH token_counts AS (
  SELECT
    btrim(regexp_replace(raw_inci_token, '\s+', ' ', 'g')) AS token,
    count(*)::int AS rows
  FROM product_ingredients
  WHERE NOT is_matched
  GROUP BY 1
),
filtered AS (
  SELECT
    token,
    rows,
    CASE
      WHEN token ~* '^(CI ?[0-9]{5}|Cl ?[0-9]{5}|red [0-9]+( lake)?|blue [0-9]+( lake)?|yellow [0-9]+( lake)?|green [0-9]+( lake)?|black [0-9]+)$' THEN 'colorant_label_variant'
      WHEN token ~* '^[A-Z][a-z]+ [A-Z][a-z]+$' THEN 'botanical_binomial_or_common_inci'
      WHEN token ~* '^(PEG|PPG)-?[0-9]|^C[0-9]+-[0-9]+|poly|hydroxy|sodium|potassium|magnesium|calcium|aluminum|zinc|bis-|acetyl|iso|methyl|ethyl|butyl|benzyl|lauryl|capryl|cetyl|cetearyl|stearyl' THEN 'chemical_name_like'
      ELSE 'ingredient_suffix_or_cosmetic_vocabulary'
    END AS reason
  FROM token_counts
  WHERE length(token) BETWEEN 3 AND 120
    AND array_length(regexp_split_to_array(token, '\s+'), 1) <= 8
    AND token !~* '[:;]|https?://|www\.|@|^(&|[0-9]+$)'
    AND token !~* '\b(apply|applying|massage|rinse|avoid|warning|caution|directions?|instructions?|ingredients?|contains?|beneficios|consideraciones|seguro|producto|skin|face|hands|children|external use|poison|store|lot|batch|code|made in|manufactured|website|packaging|keep out|do not|use only|contact with eyes|natural origin|animal testing|refill|absorbed|wrinkles|cleansed|underarms?|bedtime)\b'
    AND upper(token) NOT IN (
      'ACID','ACRYLATE','ACRYLOYLDIMETHYLTAURATE/VP','ALKYL','AMYGDALUS','ARGANIA','AVENA','BENZYL','BUTYL',
      'BUTYROSPERMUM','CAMELLIA','CAPRYLOYL','CARNAUBA','CERA','CETEARYL','CETYL','CIDO','CIRE','CITRATE',
      'COCONUT','COCOS','DEL','DIO','DIOLEATE','ELAEIS','ESTERS','EXTRACT','FD','FLOR','FLOWER','FLUORPHLOGOPITE',
      'FRUIT','GUAR','HEXYL','IN','KERNEL','LA','LAURYL','LAVANDULA','LEAF','LICO','MAGNESIUM','MADE',
      'MEDICA','MENTHA','METHYL','N-BIS','OFFICINALIS','OLEA','OLEFIN','ORGANIC','ORYZA','PALM','PARKII',
      'PEG-150','PEG-32','PEG-55','PEG-6','PPG-12','PPG-6','PPG-9','PRUNUS','PROPYL','PUNICA','RICE','ROSA',
      'ROSMARINUS','SALVIA','SATIVA','SEED','SHEA','SOJA','SPINOSA','STARCH','SULFONATE','SUNFLOWER',
      'SYNTHETIC','TAURATE','THERMAL','UNILEVER','WHEAT'
    )
    AND (
      token ~* '(acid|oil|extract|water|juice|wax|gum|butter|ferment|filtrate|starch|protein|flour|powder|salt|lactate|citrate|benzoate|sorbate|sulfate|sulfonate|stearate|palmitate|ether|esters?|glycol|glucoside|cellulose|silicone|silicate|mica|oxides?|parfum|fragrance|flavo[u]?r|vitamin|tocopher|lecithin|keratin|phytate|phospholipid|poly|hydroxy|sodium|potassium|magnesium|calcium|aluminum|zinc|lanolin|xylitol|isohexadecane|fluorphlogopite|phytate)'
      OR token ~* '^(CI ?[0-9]{5}|Cl ?[0-9]{5}|red [0-9]+|blue [0-9]+|yellow [0-9]+|green [0-9]+|black [0-9]+)$'
      OR token ~* '^(PEG|PPG)-?[0-9]|^C[0-9]+-[0-9]+'
      OR token ~* '^[A-Z][a-z]+ [A-Z][a-z]+$'
    )
)
SELECT
  CASE
    WHEN token ~* '^Cl ?[0-9]{5}$' THEN regexp_replace(token, '^Cl', 'CI', 'i')
    WHEN lower(token) = 'alpha-isomethyl lonone' THEN 'Alpha-Isomethyl Ionone'
    ELSE token
  END AS inci_name,
  token AS raw_token,
  rows,
  reason
FROM filtered;

INSERT INTO product_ingredient_cleanup_findings (
  run_label,
  reason,
  action,
  raw_inci_token,
  row_count,
  example_context
)
SELECT
  'reduce_unmatched_v1',
  reason,
  'add_missing_ingredient_or_alias_then_match',
  raw_token,
  rows,
  jsonb_build_object('canonical_inci_name', inci_name)
FROM likely_real_tokens
WHERE rows >= 2;

INSERT INTO ingredients (inci_name, slug, function_tags)
SELECT DISTINCT ON (inci_normalize(inci_name))
  inci_name,
  regexp_replace(
    lower(regexp_replace(inci_name, '[^a-zA-Z0-9]+', '-', 'g')),
    '(^-|-$)',
    '',
    'g'
  ) || '-' || left(md5(inci_name), 6),
  CASE
    WHEN inci_name ~* '(parfum|fragrance|perfume|ionone|cedrene)' THEN ARRAY['fragrance']
    WHEN inci_name ~* '(ci ?[0-9]{5}|red [0-9]|blue [0-9]|yellow [0-9]|green [0-9]|black [0-9]|mica|oxide|fluorphlogopite)' THEN ARRAY['colorant']
    WHEN inci_name ~* '(sulfate|sulfonate|glutamate|glucoside|coco|lauryl)' THEN ARRAY['surfactant']
    WHEN inci_name ~* '(oil|butter|ester|ether|isohexadecane|polyisobutene|lanolin)' THEN ARRAY['emollient']
    WHEN inci_name ~* '(gum|cellulose|starch|silicate|silylate|wax)' THEN ARRAY['texture']
    WHEN inci_name ~* '(extract|juice|protein|keratin|lecithin|phospholipid)' THEN ARRAY['skin conditioning']
    ELSE ARRAY['skin conditioning']
  END
FROM likely_real_tokens candidate
WHERE NOT EXISTS (
  SELECT 1
  FROM ingredients existing
  WHERE existing.normalized_name = inci_normalize(candidate.inci_name)
);

INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
SELECT DISTINCT ON (ingredient.id, candidate.raw_token)
  ingredient.id,
  candidate.raw_token,
  CASE WHEN candidate.raw_token <> candidate.inci_name THEN 'typo'::alias_type ELSE 'synonym'::alias_type END,
  'en',
  'manual'
FROM likely_real_tokens candidate
JOIN LATERAL (
  SELECT id
  FROM ingredients
  WHERE normalized_name = inci_normalize(candidate.inci_name)
  ORDER BY (inci_name = candidate.inci_name) DESC, created_at ASC
  LIMIT 1
) ingredient ON true
WHERE btrim(candidate.raw_token) <> ''
ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

DROP TABLE match_terms;

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

CREATE TEMP TABLE noise_tokens ON COMMIT DROP AS
SELECT
  raw_inci_token,
  count(*)::int AS rows,
  CASE
    WHEN raw_inci_token ~* '^(&quot|&lt|&gt|&amp)$' THEN 'html_entity'
    WHEN raw_inci_token ~* '^([0-9]+|[a-z]{1,2}|[A-Z]{1,2}|[*]?[A-Z0-9]{1,4})$' THEN 'code_or_short_fragment'
    WHEN raw_inci_token ~* '\b(apply|applying|massage|rinse|avoid|warning|caution|directions?|instructions?|beneficios|consideraciones|seguro|producto|skin|face|hands|children|external use|poison|store|lot|batch|code|made in|manufactured|website|packaging|keep out|do not|use only|contact with eyes|natural origin|animal testing|refill|absorbed|wrinkles|cleansed|underarms?|bedtime)\b' THEN 'instructions_or_marketing_prose'
    ELSE 'generic_fragment_or_source_noise'
  END AS reason
FROM product_ingredients
WHERE NOT is_matched
  AND (
    raw_inci_token ~* '^(&quot|&lt|&gt|&amp)$'
    OR raw_inci_token ~* '^([0-9]+|[a-z]{1,2}|[A-Z]{1,2}|[*]?[A-Z0-9]{1,4})$'
    OR raw_inci_token ~* '\b(apply|applying|massage|rinse|avoid|warning|caution|directions?|instructions?|beneficios|consideraciones|seguro|producto|skin|face|hands|children|external use|poison|store|lot|batch|code|made in|manufactured|website|packaging|keep out|do not|use only|contact with eyes|natural origin|animal testing|refill|absorbed|wrinkles|cleansed|underarms?|bedtime)\b'
    OR upper(btrim(raw_inci_token)) IN (
      'ACID','ACRYLATE','ACRYLOYLDIMETHYLTAURATE/VP','ALKYL','AMYGDALUS','ARGANIA','AVENA','BENZYL','BUTYL',
      'BUTYROSPERMUM','CAMELLIA','CAPRYLOYL','CARNAUBA','CERA','CETEARYL','CETYL','CIDO','CIRE','CITRATE',
      'COCONUT','COCOS','DEL','DIO','DIOLEATE','ELAEIS','ESTERS','EXTRACT','FD','FLOR','FLOWER','FLUORPHLOGOPITE',
      'FRUIT','GUAR','HEXYL','IN','KERNEL','LA','LAURYL','LAVANDULA','LEAF','LICO','MAGNESIUM','MADE',
      'MEDICA','MENTHA','METHYL','N-BIS','OFFICINALIS','OLEA','OLEFIN','ORGANIC','ORYZA','PALM','PARKII',
      'PEG-150','PEG-32','PEG-55','PEG-6','PPG-12','PPG-6','PPG-9','PRUNUS','PROPYL','PUNICA','RICE','ROSA',
      'ROSMARINUS','SALVIA','SATIVA','SEED','SHEA','SOJA','SPINOSA','STARCH','SULFONATE','SUNFLOWER',
      'SYNTHETIC','TAURATE','THERMAL','UNILEVER','WHEAT'
    )
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
  'reduce_unmatched_v1',
  reason,
  'delete_non_ingredient_row',
  raw_inci_token,
  rows,
  NULL
FROM noise_tokens
WHERE rows >= 2;

DELETE FROM product_ingredients pi
USING noise_tokens noise
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
  'reduce_unmatched_v1',
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
