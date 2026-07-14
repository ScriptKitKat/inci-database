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

CREATE TEMP TABLE common_alias_seed (
  canonical_name TEXT NOT NULL,
  alias TEXT NOT NULL,
  alias_type alias_type NOT NULL DEFAULT 'common',
  language TEXT NOT NULL DEFAULT 'en'
) ON COMMIT DROP;

INSERT INTO common_alias_seed (canonical_name, alias, alias_type, language)
VALUES
  ('Parfum', 'Fragance', 'typo', 'en'),
  ('Parfum', 'fragance', 'typo', 'en'),
  ('Parfum', 'Fragancia', 'translation', 'es'),
  ('Parfum', 'Partum', 'typo', 'en'),
  ('Phenoxyethanol', 'Fenoxietanol', 'translation', 'es'),
  ('Lavandula Angustifolia Oil', 'Lavender', 'common', 'en'),
  ('Prunus Armeniaca Kernel Oil', 'Apricot', 'common', 'en'),
  ('Glycine Soja Oil', 'Soybean', 'common', 'en'),
  ('Citrus Aurantium Bergamia Peel Oil', 'Bergamot', 'common', 'en'),
  ('Mentha Piperita Oil', 'Peppermint', 'common', 'en'),
  ('Mentha Viridis Leaf Oil', 'Spearmint', 'common', 'en'),
  ('Rosmarinus Officinalis Leaf Extract', 'Rosemary', 'common', 'en'),
  ('Chamomilla Recutita Flower Extract', 'Chamomile', 'common', 'en'),
  ('Simmondsia Chinensis Seed Oil', 'Jojoba', 'common', 'en'),
  ('Ricinus Communis Seed Oil', 'Castor', 'common', 'en'),
  ('Citrus Aurantium Dulcis Peel Oil', 'Orange', 'common', 'en'),
  ('Citrus Limon Peel Oil', 'Lemon', 'common', 'en'),
  ('Olea Europaea Fruit Oil', 'Olive', 'common', 'en'),
  ('Beeswax', 'Cire Dabeille', 'translation', 'fr'),
  ('Beeswax', 'CIRE DABEILLE', 'translation', 'fr'),
  ('Beeswax', 'CIRE D''ABEILLE', 'translation', 'fr'),
  ('Candelilla Wax', 'Candelilla', 'common', 'en'),
  ('AQUA', 'Aqua/Eau', 'translation', 'fr'),
  ('Titanium Dioxide', '77891/TITANIUM', 'synonym', 'en'),
  ('CI 19140', '19140/YELLOW', 'synonym', 'en'),
  ('CI 42090', '42090/BLUE', 'synonym', 'en'),
  ('CI 14700', '14700/RED', 'synonym', 'en');

CREATE TEMP TABLE common_ingredient_seed (
  inci_name TEXT PRIMARY KEY,
  function_tag TEXT NOT NULL
) ON COMMIT DROP;

INSERT INTO common_ingredient_seed (inci_name, function_tag)
VALUES
  ('Mentha Viridis Leaf Oil', 'fragrance'),
  ('Citrus Aurantium Bergamia Peel Oil', 'fragrance'),
  ('CI 14700', 'colorant');

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
FROM common_ingredient_seed seed
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
FROM common_alias_seed alias_seed
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

CREATE TEMP TABLE broad_likely_ingredients ON COMMIT DROP AS
WITH token_counts AS (
  SELECT
    btrim(regexp_replace(raw_inci_token, '\s+', ' ', 'g')) AS token,
    count(*)::int AS rows
  FROM product_ingredients
  WHERE NOT is_matched
  GROUP BY 1
)
SELECT
  token AS inci_name,
  rows,
  CASE
    WHEN token ~* '^[A-Z][a-z]+ [A-Z][a-z]+($| )' THEN 'botanical_or_inci_name_from_adjacent_context'
    WHEN token ~* '^(PEG|PPG|CI|Cl|C[0-9])' THEN 'inci_code_or_polymer_label'
    ELSE 'short_cosmetic_ingredient_like_token'
  END AS reason
FROM token_counts
WHERE length(token) BETWEEN 3 AND 100
  AND array_length(regexp_split_to_array(btrim(token), '\s+'), 1) <= 8
  AND token ~ '^[[:alnum:] /.,+()''’*-]+$'
  AND token !~* '\b(apply|massage|rinse|avoid|warning|caution|directions?|instructions?|beneficios|consideraciones|seguro|producto|children|external use|poison|store|lot|batch|code|made in|manufactured|website|packaging|keep out|do not|use only|contact with eyes|natural origin|animal testing|refill|absorbed|wrinkles|cleansed|underarms?|bedtime|continued|certified|agriculture|biologique|conservateur|agents de surface|ppm|mg|envase|mexico|before|after|suitable|daily|twice|shake|spray|swallow|toothbrush|cream|creme|developer|hoitoaine|rgcreme|unilever|avene)\b'
  AND token !~* '^(&|[0-9]+$|[*]?[A-Z0-9]{1,5}$)'
  AND upper(btrim(token)) NOT IN (
    'BLACK','COLOR','NATURAL','VEGETABLE','HUILE','EXTRAIT','SAVON','DUFTSTOFFE','CIRE','ABEILLE',
    'DABEILLE','MARIS','ACRYLOYLDIMETHYL','LAUROYL','STEARYL','COCAMIDOPROPYL','TRIGLYCERIDE',
    'VIOLET','PHOSPHATE','ACRYLATES','EUCALYPTUS','ZINGIBER','CHAMOMILLA','THEOBROMA','EDETATO',
    'LIMON','NUCIFERA','STEROLS','METHACRYLATE','SILYLATE','CERIFERA','AMINO','METHYLENE',
    'PROPYLENE','PASSIFLORA','ENZYME','CAPRYLYL','BIS-BENZOTRIAZOLYL','BAMBUSA','AMARA','MYRISTATE',
    'CARTHAMUS','BRASSICA','HAMAMELIS','SESAMUM','GLYCERIDES','PIPERITA','TETRAMETHYLBUTYLPHENOL',
    'HELIANTHUS','SUGAR','RAPESEED','CAMPESTRIS','METHICONE','OLEYL','CARICA','CHINENSIS','ANTES',
    'COLLE','CAPRYLIC/CAPRIC','LINUM','METHOXY','CARBONATE','PG-BETAINE','HYDRO','ALTHAEA',
    'HIBISCUS','SACCHARUM','THYMUS','ACETYL','COCOYL','DIETHYLAMINO','CUCUMIS'
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
  'reduce_unmatched_v2',
  reason,
  'add_provisional_ingredient_then_match',
  inci_name,
  rows,
  NULL
FROM broad_likely_ingredients
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
    WHEN inci_name ~* '(ci ?[0-9]{5}|red|blue|yellow|green|black|violet|titanium)' THEN ARRAY['colorant']
    WHEN inci_name ~* '(parfum|fragrance|fragance|perfume|duft|aroma)' THEN ARRAY['fragrance']
    WHEN inci_name ~* '(sulfate|sulfonate|glutamate|glucoside|betaine|cocamidopropyl|lauroyl|cocoyl)' THEN ARRAY['surfactant']
    WHEN inci_name ~* '(oil|butter|wax|ester|ether|myristate|caprylate|dicaprate|triglyceride|dimethicone)' THEN ARRAY['emollient']
    WHEN inci_name ~* '(gum|cellulose|starch|silicate|silylate|acrylate|phosphate|poloxamer)' THEN ARRAY['texture']
    ELSE ARRAY['skin conditioning']
  END
FROM broad_likely_ingredients candidate
WHERE NOT EXISTS (
  SELECT 1
  FROM ingredients existing
  WHERE existing.normalized_name = inci_normalize(candidate.inci_name)
);

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

CREATE TEMP TABLE broad_noise_tokens ON COMMIT DROP AS
SELECT
  raw_inci_token,
  count(*)::int AS rows,
  CASE
    WHEN raw_inci_token ~* '^(&|[0-9]+$|[*]?[A-Z0-9]{1,6}$|[a-z]{1,2}$|[A-Z]{1,2}$)' THEN 'code_or_short_fragment'
    WHEN raw_inci_token ~* '\b(apply|massage|rinse|avoid|warning|caution|directions?|instructions?|beneficios|consideraciones|seguro|producto|children|external use|poison|store|lot|batch|code|made in|manufactured|website|packaging|keep out|do not|use only|contact with eyes|natural origin|animal testing|refill|absorbed|wrinkles|cleansed|underarms?|bedtime|continued|certified|agriculture|biologique|conservateur|agents de surface|ppm|mg|envase|mexico|before|after|suitable|daily|twice|shake|spray|swallow|toothbrush|cream|creme|developer|hoitoaine|rgcreme|unilever|avene)\b' THEN 'prose_or_packaging_text'
    ELSE 'generic_unresolved_fragment'
  END AS reason
FROM product_ingredients
WHERE NOT is_matched
  AND (
    raw_inci_token ~* '^(&|[0-9]+$|[*]?[A-Z0-9]{1,6}$|[a-z]{1,2}$|[A-Z]{1,2}$)'
    OR raw_inci_token ~* '\b(apply|massage|rinse|avoid|warning|caution|directions?|instructions?|beneficios|consideraciones|seguro|producto|children|external use|poison|store|lot|batch|code|made in|manufactured|website|packaging|keep out|do not|use only|contact with eyes|natural origin|animal testing|refill|absorbed|wrinkles|cleansed|underarms?|bedtime|continued|certified|agriculture|biologique|conservateur|agents de surface|ppm|mg|envase|mexico|before|after|suitable|daily|twice|shake|spray|swallow|toothbrush|cream|creme|developer|hoitoaine|rgcreme|unilever|avene)\b'
    OR upper(btrim(raw_inci_token)) IN (
      'BLACK','COLOR','NATURAL','VEGETABLE','HUILE','EXTRAIT','SAVON','DUFTSTOFFE','CIRE','ABEILLE',
      'DABEILLE','MARIS','ACRYLOYLDIMETHYL','LAUROYL','STEARYL','COCAMIDOPROPYL','TRIGLYCERIDE',
      'VIOLET','PHOSPHATE','ACRYLATES','EUCALYPTUS','ZINGIBER','CHAMOMILLA','THEOBROMA','EDETATO',
      'LIMON','NUCIFERA','STEROLS','METHACRYLATE','SILYLATE','CERIFERA','AMINO','METHYLENE',
      'PROPYLENE','PASSIFLORA','ENZYME','CAPRYLYL','BIS-BENZOTRIAZOLYL','BAMBUSA','AMARA','MYRISTATE',
      'CARTHAMUS','BRASSICA','HAMAMELIS','SESAMUM','GLYCERIDES','PIPERITA','TETRAMETHYLBUTYLPHENOL',
      'HELIANTHUS','SUGAR','RAPESEED','CAMPESTRIS','METHICONE','OLEYL','CARICA','CHINENSIS','ANTES',
      'COLLE','CAPRYLIC/CAPRIC','LINUM','METHOXY','CARBONATE','PG-BETAINE','HYDRO','ALTHAEA',
      'HIBISCUS','SACCHARUM','THYMUS','ACETYL','COCOYL','DIETHYLAMINO','CUCUMIS'
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
  'reduce_unmatched_v2',
  reason,
  'delete_non_ingredient_row',
  raw_inci_token,
  rows,
  NULL
FROM broad_noise_tokens
WHERE rows >= 2;

DELETE FROM product_ingredients pi
USING broad_noise_tokens noise
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
  'reduce_unmatched_v2',
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
