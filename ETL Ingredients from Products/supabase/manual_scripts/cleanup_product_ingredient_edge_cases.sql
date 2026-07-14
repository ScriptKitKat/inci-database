BEGIN;

SET LOCAL statement_timeout = '10min';

CREATE TEMP TABLE approved_ingredient_seed (
  inci_name TEXT PRIMARY KEY,
  function_tag TEXT
) ON COMMIT DROP;

INSERT INTO approved_ingredient_seed (inci_name, function_tag)
VALUES
  ('Acrylates/C10-30 Alkyl Acrylate Crosspolymer', 'texture'),
  ('Acacia Senegal Gum', 'texture'),
  ('Adipic Acid/Neopentyl Glycol/Trimellitic Anhydride Copolymer', 'film forming'),
  ('Aloe Barbadensis Leaf Juice', 'skin conditioning'),
  ('Avena Sativa Kernel Extract', 'skin conditioning'),
  ('Avena Sativa Kernel Flour', 'skin conditioning'),
  ('Beeswax', 'texture'),
  ('Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine', 'uv filter'),
  ('Butyrospermum Parkii Butter', 'emollient'),
  ('C12-15 Alkyl Benzoate', 'emollient'),
  ('Caprylic/Capric Triglyceride', 'emollient'),
  ('Carnauba Wax', 'texture'),
  ('Candelilla Wax', 'texture'),
  ('Charcoal Powder', 'absorbent'),
  ('Chamomilla Recutita Flower Extract', 'skin conditioning'),
  ('Citrus Aurantium Dulcis Peel Oil', 'fragrance'),
  ('Citrus Aurantium Peel Oil', 'fragrance'),
  ('Citrus Limon Peel Oil', 'fragrance'),
  ('Cocoa Seed Butter', 'emollient'),
  ('Coco-Caprylate/Caprate', 'emollient'),
  ('Cocos Nucifera Fruit Extract', 'skin conditioning'),
  ('Cocos Nucifera Oil', 'emollient'),
  ('Copernicia Cerifera Wax', 'texture'),
  ('Eucalyptus Globulus Leaf Oil', 'fragrance'),
  ('Glyceryl Glucoside', 'humectant'),
  ('Glycine Soja Oil', 'emollient'),
  ('Glycine Soja Seed Extract', 'skin conditioning'),
  ('Glycine Soja Sterols', 'skin conditioning'),
  ('Helianthus Annuus Seed Oil', 'emollient'),
  ('Hydrogenated Castor Oil', 'texture'),
  ('Hydrogenated Glyceryl Palmate', 'emollient'),
  ('Hydrogenated Rapeseed Oil', 'emollient'),
  ('Hydrolyzed Corn Protein', 'hair conditioning'),
  ('Hydrolyzed Milk Protein', 'skin conditioning'),
  ('Hydrolyzed Soy Protein', 'skin conditioning'),
  ('Hydrolyzed Wheat Protein', 'skin conditioning'),
  ('Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer', 'texture'),
  ('Hydroxypropyl Starch Phosphate', 'texture'),
  ('Iron Oxides', 'colorant'),
  ('Lavandula Angustifolia Oil', 'fragrance'),
  ('Leuconostoc/Radish Root Ferment Filtrate', 'preservative'),
  ('Melaleuca Alternifolia Leaf Oil', 'fragrance'),
  ('Mentha Piperita Oil', 'fragrance'),
  ('Magnesium Stearate', 'texture'),
  ('Olea Europaea Fruit Oil', 'emollient'),
  ('Oryza Sativa Starch', 'absorbent'),
  ('Panax Ginseng Root Extract', 'skin conditioning'),
  ('PEG-6 Caprylic/Capric Glycerides', 'surfactant'),
  ('PEG-40 Hydrogenated Castor Oil', 'surfactant'),
  ('PEG-60 Hydrogenated Castor Oil', 'surfactant'),
  ('PEG-200 Hydrogenated Glyceryl Palmate', 'surfactant'),
  ('Pentaerythrityl Tetra-Di-T-Butyl Hydroxyhydrocinnamate', 'antioxidant'),
  ('Persea Gratissima Oil', 'emollient'),
  ('Pogostemon Cablin Oil', 'fragrance'),
  ('Prunus Amygdalus Dulcis Oil', 'emollient'),
  ('Prunus Armeniaca Kernel Oil', 'emollient'),
  ('PVM/MA Copolymer', 'film forming'),
  ('Ricinus Communis Seed Oil', 'emollient'),
  ('Rosmarinus Officinalis Leaf Extract', 'antioxidant'),
  ('Rosmarinus Officinalis Leaf Oil', 'fragrance'),
  ('Saccharum Officinarum Extract', 'skin conditioning'),
  ('Sesamum Indicum Seed Oil', 'emollient'),
  ('Simmondsia Chinensis Seed Oil', 'emollient'),
  ('Sodium C14-16 Olefin Sulfonate', 'surfactant'),
  ('Sodium Carbomer', 'texture'),
  ('Sodium Cetearyl Sulfate', 'surfactant'),
  ('Sodium Coco-Sulfate', 'surfactant'),
  ('Sodium Hydroxide', 'ph adjuster'),
  ('Sodium Polyacrylate', 'texture'),
  ('Sodium PCA', 'humectant'),
  ('Sodium Starch Octenylsuccinate', 'absorbent'),
  ('Synthetic Wax', 'texture'),
  ('TEA-Dodecylbenzenesulfonate', 'surfactant'),
  ('TEA-Sulfate', 'surfactant'),
  ('Theobroma Cacao Seed Butter', 'emollient'),
  ('Toluene-2,5-Diamine', 'hair dye'),
  ('Trideceth-2 Carboxamide MEA', 'surfactant'),
  ('Vitis Vinifera Seed Oil', 'emollient'),
  ('Zea Mays Starch', 'absorbent'),
  ('Zinc Oxide', 'uv filter'),
  ('Zinc PCA', 'skin conditioning'),
  ('2-Hexanediol', 'solvent'),
  ('2-Oleamido-1,3-Octadecanediol', 'skin conditioning'),
  ('Blue 1', 'colorant'),
  ('Blue 1 Lake', 'colorant'),
  ('Black 2', 'colorant'),
  ('Green 3', 'colorant'),
  ('Green 5', 'colorant'),
  ('Red 4', 'colorant'),
  ('Red 6', 'colorant'),
  ('Red 7', 'colorant'),
  ('Red 7 Lake', 'colorant'),
  ('Red 22 Lake', 'colorant'),
  ('Red 28 Lake', 'colorant'),
  ('Red 30 Lake', 'colorant'),
  ('Red 33', 'colorant'),
  ('Red 33 Lake', 'colorant'),
  ('Yellow 5 Lake', 'colorant'),
  ('Yellow 6', 'colorant'),
  ('Yellow 6 Lake', 'colorant'),
  ('CI 19140', 'colorant'),
  ('CI 42090', 'colorant'),
  ('CI 77019', 'colorant'),
  ('CI 77266', 'colorant'),
  ('CI 77491', 'colorant'),
  ('CI 77492', 'colorant'),
  ('CI 77499', 'colorant'),
  ('CI 77891', 'colorant'),
  ('CI 77947', 'colorant');

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
FROM approved_ingredient_seed seed
WHERE NOT EXISTS (
  SELECT 1
  FROM ingredients existing
  WHERE existing.normalized_name = inci_normalize(seed.inci_name)
);

CREATE TEMP TABLE approved_alias_seed (
  canonical_name TEXT NOT NULL,
  alias TEXT NOT NULL,
  alias_type alias_type NOT NULL DEFAULT 'synonym',
  language TEXT NOT NULL DEFAULT 'en'
) ON COMMIT DROP;

INSERT INTO approved_alias_seed (canonical_name, alias, alias_type, language)
VALUES
  ('AQUA', 'Aqua/Water', 'synonym', 'en'),
  ('AQUA', 'Aqua / Water', 'synonym', 'en'),
  ('AQUA', 'Aqua/Water/Eau', 'synonym', 'en'),
  ('AQUA', 'AQUA/WATER/EAU', 'synonym', 'en'),
  ('AQUA', 'Water/Aqua/Eau', 'synonym', 'en'),
  ('AQUA', 'Water/Eau', 'synonym', 'en'),
  ('AQUA', 'Aqua Water', 'synonym', 'en'),
  ('Acrylates/C10-30 Alkyl Acrylate Crosspolymer', 'ACRYLATES/C10-30 ALKYL ACRYLATE CROSSPOLYMER', 'synonym', 'en'),
  ('Aloe Barbadensis Leaf Juice', 'Aloe Barbadensis Leaf Juice*', 'synonym', 'en'),
  ('Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine', 'BIS-ETHYLHEXYLOXYPHENOL METHOXYPHENYL TRIAZINE', 'synonym', 'en'),
  ('Butyrospermum Parkii Butter', 'Shea Butter', 'common', 'en'),
  ('Butyrospermum Parkii Butter', 'Butyrospermum Parkii', 'synonym', 'en'),
  ('Butyrospermum Parkii Butter', 'Butyrospermum Parkii Butter Shea Butter', 'synonym', 'en'),
  ('Butyrospermum Parkii Butter', 'BUTYROSPERMUM PARKII BUTTER/SHEA BUTTER', 'synonym', 'en'),
  ('Butyrospermum Parkii Butter', 'BUTTER/SHEA BUTTER', 'synonym', 'en'),
  ('Butyrospermum Parkii Butter', 'beurre de karite', 'translation', 'fr'),
  ('Butyrospermum Parkii Butter', 'beurre de karité', 'translation', 'fr'),
  ('Caprylic/Capric Triglyceride', 'Caprylic Capric Triglyceride', 'synonym', 'en'),
  ('Carnauba Wax', 'Cera Carnauba Wax', 'synonym', 'en'),
  ('Carnauba Wax', 'Copernicia Cerifera Cera Carnauba Wax', 'synonym', 'en'),
  ('Carnauba Wax', 'Copernicia Cerifera Cera', 'synonym', 'en'),
  ('Carnauba Wax', 'cera de carnauba', 'translation', 'pt'),
  ('Beeswax', 'Cera de abelha', 'translation', 'pt'),
  ('Chamomilla Recutita Flower Extract', 'Chamomilla Recutita Matricaria Flower Extract', 'synonym', 'en'),
  ('Chamomilla Recutita Flower Extract', 'Matricaria Flower Extract', 'common', 'en'),
  ('Citrus Aurantium Dulcis Peel Oil', 'Citrus Aurantium Dulcis Orange Peel Oil', 'synonym', 'en'),
  ('Citrus Aurantium Dulcis Peel Oil', 'Orange Peel Oil', 'common', 'en'),
  ('Citrus Limon Peel Oil', 'Lemon Peel Oil', 'common', 'en'),
  ('Cocos Nucifera Oil', 'Coconut Oil', 'common', 'en'),
  ('Cocos Nucifera Oil', 'Cocos Nucifera', 'synonym', 'en'),
  ('Cocos Nucifera Oil', 'Cocos Nucifera Coconut Oil', 'synonym', 'en'),
  ('Cocos Nucifera Oil', 'COCOS NUCIFERA OIL/COCONUT OIL', 'synonym', 'en'),
  ('Copernicia Cerifera Wax', 'Copernicia Cerifera Cera', 'synonym', 'en'),
  ('Glycine Soja Oil', 'Soybean Oil', 'common', 'en'),
  ('Glycine Soja Oil', 'Glycine Soja', 'synonym', 'en'),
  ('Glycine Soja Oil', 'Glycine Soja Soybean Oil', 'synonym', 'en'),
  ('Glycine Soja Seed Extract', 'Soybean Seed Extract', 'common', 'en'),
  ('Glycine Soja Seed Extract', 'Glycine Soja Soybean Seed Extract', 'synonym', 'en'),
  ('Glycine Soja Sterols', 'Glycine Soja Soybean Sterols', 'synonym', 'en'),
  ('Helianthus Annuus Seed Oil', 'Sunflower Seed Oil', 'common', 'en'),
  ('Helianthus Annuus Seed Oil', 'Helianthus Annuus Seed Oil Sunflower Seed Oil', 'synonym', 'en'),
  ('Helianthus Annuus Seed Oil', 'Helianthus Annuus Seed Oil / Sunflower Seed Oil', 'synonym', 'en'),
  ('Helianthus Annuus Seed Oil', 'huile de tournesol', 'translation', 'fr'),
  ('Hydrolyzed Corn Protein', 'Corn Protein Hydrolyzed', 'synonym', 'en'),
  ('Hydrolyzed Soy Protein', 'Hydrolyzed Soy Protein', 'synonym', 'en'),
  ('Hydrolyzed Soy Protein', 'Hydrolyzed Soy Protein Hydrolyzed', 'synonym', 'en'),
  ('Hydrolyzed Wheat Protein', 'Hydrolyzed Wheat Protein', 'synonym', 'en'),
  ('Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer', 'HYDROXYETHYL ACRYLATE/SODIUM ACRYLOYLDIMETHYL TAURATE COPOLYMER', 'synonym', 'en'),
  ('Iron Oxides', 'Iron Oxides', 'synonym', 'en'),
  ('Lavandula Angustifolia Oil', 'Lavandula Angustifolia Lavender Oil', 'synonym', 'en'),
  ('Lavandula Angustifolia Oil', 'Lavender Oil', 'common', 'en'),
  ('Leuconostoc/Radish Root Ferment Filtrate', 'LEUCONOSTOC/RADISH ROOT FERMENT FILTRATE', 'synonym', 'en'),
  ('Melaleuca Alternifolia Leaf Oil', 'Melaleuca Alternifolia Tea Tree Leaf Oil', 'synonym', 'en'),
  ('Melaleuca Alternifolia Leaf Oil', 'Tea Tree Leaf Oil', 'common', 'en'),
  ('Mentha Piperita Oil', 'Peppermint Oil', 'common', 'en'),
  ('Magnesium Stearate', 'stéarate de magnésium', 'translation', 'fr'),
  ('Olea Europaea Fruit Oil', 'Olive Fruit Oil', 'common', 'en'),
  ('Olea Europaea Fruit Oil', 'Olea Europaea', 'synonym', 'en'),
  ('Olea Europaea Fruit Oil', 'Olea Europaea Olive Fruit Oil', 'synonym', 'en'),
  ('Oryza Sativa Starch', 'Oryza Sativa Rice Starch', 'synonym', 'en'),
  ('PEG-40 Hydrogenated Castor Oil', 'PEG-40 HYDROGENATED CASTOR OIL', 'synonym', 'en'),
  ('PEG-60 Hydrogenated Castor Oil', 'PEG-60 HYDROGENATED CASTOR OIL', 'synonym', 'en'),
  ('PEG-200 Hydrogenated Glyceryl Palmate', 'PEG-200 HYDROGENATED GLYCERYL PALMATE', 'synonym', 'en'),
  ('Persea Gratissima Oil', 'Persea Gratissima Avocado Oil', 'synonym', 'en'),
  ('Persea Gratissima Oil', 'Avocado Oil', 'common', 'en'),
  ('Prunus Amygdalus Dulcis Oil', 'Sweet Almond Oil', 'common', 'en'),
  ('Prunus Amygdalus Dulcis Oil', 'Prunus Amygdalus Dulcis', 'synonym', 'en'),
  ('Prunus Amygdalus Dulcis Oil', 'Prunus Amygdalus Dulcis Sweet Almond Oil', 'synonym', 'en'),
  ('Prunus Armeniaca Kernel Oil', 'Apricot Kernel Oil', 'common', 'en'),
  ('Prunus Armeniaca Kernel Oil', 'Prunus Armeniaca Kernel Oil / Apricot Kernel Oil', 'synonym', 'en'),
  ('Ricinus Communis Seed Oil', 'Castor Oil', 'common', 'en'),
  ('Ricinus Communis Seed Oil', 'Castor Seed Oil', 'common', 'en'),
  ('Rosmarinus Officinalis Leaf Extract', 'Rosemary Leaf Extract', 'common', 'en'),
  ('Rosmarinus Officinalis Leaf Extract', 'Rosmarinus Officinalis Rosemary Leaf Extract', 'synonym', 'en'),
  ('Rosmarinus Officinalis Leaf Oil', 'Rosmarinus Officinalis Rosemary Leaf Oil', 'synonym', 'en'),
  ('Saccharum Officinarum Extract', 'Saccharum Officinarum Extract Sugar Cane Extract', 'synonym', 'en'),
  ('Saccharum Officinarum Extract', 'Sugar Cane Extract', 'common', 'en'),
  ('Sesamum Indicum Seed Oil', 'Sesame Seed Oil', 'common', 'en'),
  ('Simmondsia Chinensis Seed Oil', 'Jojoba Seed Oil', 'common', 'en'),
  ('Simmondsia Chinensis Seed Oil', 'Simmondsia Chinensis', 'synonym', 'en'),
  ('Simmondsia Chinensis Seed Oil', 'Simmondsia Chinensis Jojoba Seed Oil', 'synonym', 'en'),
  ('Sodium Hydroxide', 'Hidróxido de Sódio', 'translation', 'pt'),
  ('Sodium Polyacrylate', 'polyacrylate de sodium', 'translation', 'fr'),
  ('Theobroma Cacao Seed Butter', 'Cocoa Seed Butter', 'common', 'en'),
  ('Toluene-2,5-Diamine', 'TOLUENE-2 5-DIAMINE', 'synonym', 'en'),
  ('Trideceth-2 Carboxamide MEA', 'TRIDECETH-2 CARBOXAMIDE MEA', 'synonym', 'en'),
  ('Vitis Vinifera Seed Oil', 'Grape Seed Oil', 'common', 'en'),
  ('Zea Mays Starch', 'Corn Starch', 'common', 'en'),
  ('Zea Mays Starch', 'Zea Mays Corn Starch', 'synonym', 'en'),
  ('Zinc Oxide', 'Óxido de zinco', 'translation', 'pt'),
  ('Zinc PCA', 'Zinc PCA', 'synonym', 'en'),
  ('2-Oleamido-1,3-Octadecanediol', '2-OLEAMIDO-1 3-OCTADECANEDIOL', 'synonym', 'en'),
  ('Blue 1', 'FD&C Blue No. 1', 'synonym', 'en'),
  ('Blue 1', 'CI42090', 'synonym', 'en'),
  ('Blue 1', 'CI 42090', 'synonym', 'en'),
  ('CI 19140', '19140', 'synonym', 'en'),
  ('CI 42090', '42090', 'synonym', 'en'),
  ('CI 77019', '77019', 'synonym', 'en'),
  ('CI 77266', '77266', 'synonym', 'en'),
  ('CI 77491', '77491', 'synonym', 'en'),
  ('CI 77492', '77492', 'synonym', 'en'),
  ('CI 77499', '77499', 'synonym', 'en'),
  ('CI 77891', '77891', 'synonym', 'en'),
  ('CI 77891', 'CI77891', 'synonym', 'en'),
  ('CI 77947', '77947', 'synonym', 'en');

INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
SELECT
  ingredient.id,
  alias_seed.alias,
  alias_seed.alias_type,
  alias_seed.language,
  'manual'
FROM approved_alias_seed alias_seed
JOIN LATERAL (
  SELECT id
  FROM ingredients
  WHERE normalized_name = inci_normalize(alias_seed.canonical_name)
  ORDER BY (inci_name = alias_seed.canonical_name) DESC, created_at ASC
  LIMIT 1
) ingredient ON true
WHERE btrim(alias_seed.alias) <> ''
ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

DELETE FROM ingredient_aliases
WHERE btrim(coalesce(normalized_alias, '')) = '';

CREATE TEMP TABLE product_ingredient_match_terms ON COMMIT DROP AS
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

CREATE TEMP TABLE product_ingredient_may_contain_start ON COMMIT DROP AS
SELECT product_id, min(position) AS start_position
FROM product_ingredients
WHERE raw_inci_token ~* '\mmay\s*contain\M'
   OR raw_inci_token ~* '\mpeut\s*contenir\M'
   OR upper(btrim(raw_inci_token)) = 'MAY'
   OR upper(btrim(raw_inci_token)) = 'CONTAIN/PEUT'
GROUP BY product_id;

DELETE FROM product_ingredients pi
USING product_ingredient_may_contain_start start
WHERE pi.product_id = start.product_id
  AND pi.position >= start.start_position;

DELETE FROM product_ingredients
WHERE NOT is_matched
  AND (
    raw_inci_token ~ '^[A-Za-z]$'
    OR inci_normalize(raw_inci_token) IN (
      'beneficios',
      'consideraciones',
      'contain',
      'de',
      'fil',
      'ingredients',
      'ingredient',
      'ingr',
      'ngredients',
      'no',
      'peut',
      'contenir'
    )
    OR raw_inci_token ~* 'ingredient lists for the products of our brand are updated regularly'
    OR raw_inci_token ~* 'please refer to the ingredient list'
    OR raw_inci_token ~* 'puede causar'
    OR raw_inci_token ~* 'no hay contraindicaciones'
    OR raw_inci_token ~* '^agente '
    OR raw_inci_token ~* '^\* ?(ingredients|ingrédients|issus|ingredient)'
    OR raw_inci_token ~* '^f\.?i\.?l\.? '
    OR raw_inci_token ~* '^de-[0-9]'
  );

CREATE TEMP TABLE product_ingredient_renumber ON COMMIT DROP AS
SELECT
  id,
  row_number() OVER (PARTITION BY product_id ORDER BY position, id)::int AS new_position
FROM product_ingredients;

UPDATE product_ingredients pi
SET position = -renumber.new_position
FROM product_ingredient_renumber renumber
WHERE pi.id = renumber.id;

UPDATE product_ingredients
SET position = -position
WHERE position < 0;

DROP TABLE product_ingredient_renumber;

CREATE TEMP TABLE approved_sequence_repair (
  merged_token TEXT NOT NULL,
  parts TEXT[] NOT NULL,
  ingredient_id UUID
) ON COMMIT DROP;

INSERT INTO approved_sequence_repair (merged_token, parts, ingredient_id)
SELECT
  seed.merged_token,
  ARRAY(SELECT inci_normalize(part) FROM unnest(seed.parts) AS part),
  terms.ingredient_id
FROM (
  VALUES
    ('PEG-40 Hydrogenated Castor Oil', ARRAY['PEG-40', 'HYDROGENATED', 'CASTOR OIL']),
    ('PEG-60 Hydrogenated Castor Oil', ARRAY['PEG-60', 'HYDROGENATED', 'CASTOR OIL']),
    ('PEG-200 Hydrogenated Glyceryl Palmate', ARRAY['PEG-200', 'HYDROGENATED', 'GLYCERYL', 'PALMATE']),
    ('Hydrogenated Glyceryl Palmate', ARRAY['HYDROGENATED', 'GLYCERYL', 'PALMATE']),
    ('Acrylates/C10-30 Alkyl Acrylate Crosspolymer', ARRAY['ACRYLATES/C10-30', 'ALKYL', 'ACRYLATE', 'CROSSPOLYMER']),
    ('Pentaerythrityl Tetra-Di-T-Butyl Hydroxyhydrocinnamate', ARRAY['PENTAERYTHRITYL', 'TETRA-DI-T-BUTYL', 'HYDROXYHYDROCINNAMATE']),
    ('Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine', ARRAY['BIS-ETHYLHEXYLOXYPHENOL', 'METHOXYPHENYL', 'TRIAZINE']),
    ('Hydrolyzed Wheat Protein', ARRAY['HYDROLYZED', 'WHEAT', 'PROTEIN']),
    ('Hydrolyzed Soy Protein', ARRAY['HYDROLYZED', 'SOY', 'PROTEIN']),
    ('Hydrolyzed Corn Protein', ARRAY['HYDROLYZED', 'CORN', 'PROTEIN']),
    ('Trideceth-2 Carboxamide MEA', ARRAY['TRIDECETH-2', 'CARBOXAMIDE', 'MEA']),
    ('Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer', ARRAY['HYDROXYETHYL', 'ACRYLATE/SODIUM', 'ACRYLOYLDIMETHYL', 'TAURATE', 'COPOLYMER']),
    ('2-Oleamido-1,3-Octadecanediol', ARRAY['2-OLEAMIDO-1', '3-OCTADECANEDIOL']),
    ('Toluene-2,5-Diamine', ARRAY['TOLUENE-2', '5-DIAMINE']),
    ('Prunus Amygdalus Dulcis Oil', ARRAY['PRUNUS', 'AMYGDALUS', 'DULCIS']),
    ('Prunus Amygdalus Dulcis Oil', ARRAY['PRUNUS AMYGDALUS DULCIS', 'SWEET ALMOND OIL']),
    ('Olea Europaea Fruit Oil', ARRAY['OLEA', 'EUROPAEA', 'FRUIT OIL']),
    ('Olea Europaea Fruit Oil', ARRAY['OLEA EUROPAEA', 'OLIVE', 'FRUIT OIL']),
    ('Cocos Nucifera Oil', ARRAY['COCOS NUCIFERA', 'COCONUT OIL']),
    ('Simmondsia Chinensis Seed Oil', ARRAY['SIMMONDSIA CHINENSIS', 'JOJOBA SEED OIL']),
    ('Helianthus Annuus Seed Oil', ARRAY['HELIANTHUS ANNUUS SEED OIL', 'SUNFLOWER SEED OIL']),
    ('Glycine Soja Oil', ARRAY['GLYCINE SOJA', 'SOYBEAN OIL']),
    ('Avena Sativa Kernel Extract', ARRAY['AVENA SATIVA', 'OAT', 'KERNEL EXTRACT']),
    ('Avena Sativa Kernel Flour', ARRAY['AVENA SATIVA', 'OAT', 'KERNEL FLOUR']),
    ('Zea Mays Starch', ARRAY['ZEA', 'MAYS', 'STARCH']),
    ('Zea Mays Starch', ARRAY['ZEA MAYS', 'CORN', 'STARCH']),
    ('Oryza Sativa Starch', ARRAY['ORYZA', 'SATIVA', 'STARCH']),
    ('Oryza Sativa Starch', ARRAY['ORYZA SATIVA', 'RICE', 'STARCH']),
    ('Acacia Senegal Gum', ARRAY['ACACIA', 'SENEGAL', 'GUM']),
    ('Copernicia Cerifera Wax', ARRAY['COPERNICIA', 'CERIFERA', 'CERA']),
    ('Melaleuca Alternifolia Leaf Oil', ARRAY['MELALEUCA ALTERNIFOLIA', 'TEA TREE', 'LEAF OIL']),
    ('Lavandula Angustifolia Oil', ARRAY['LAVANDULA ANGUSTIFOLIA', 'LAVENDER OIL']),
    ('Rosmarinus Officinalis Leaf Extract', ARRAY['ROSMARINUS OFFICINALIS', 'ROSEMARY LEAF EXTRACT']),
    ('Rosmarinus Officinalis Leaf Oil', ARRAY['ROSMARINUS OFFICINALIS', 'ROSEMARY', 'LEAF OIL']),
    ('Citrus Aurantium Dulcis Peel Oil', ARRAY['CITRUS AURANTIUM DULCIS', 'ORANGE PEEL OIL']),
    ('Prunus Armeniaca Kernel Oil', ARRAY['PRUNUS ARMENIACA', 'APRICOT KERNEL OIL']),
    ('Saccharum Officinarum Extract', ARRAY['SACCHARUM', 'OFFICINARUM EXTRACT', 'SUGAR', 'CANE EXTRACT']),
    ('Leuconostoc/Radish Root Ferment Filtrate', ARRAY['LEUCONOSTOC/RADISH', 'ROOT FERMENT', 'FILTRATE']),
    ('Adipic Acid/Neopentyl Glycol/Trimellitic Anhydride Copolymer', ARRAY['ADIPIC', 'ACID/NEOPENTYL', 'GLYCOL/TRIMELLITIC', 'ANHYDRIDE', 'COPOLYMER']),
    ('Red 28 Lake', ARRAY['RED', '28', 'LAKE']),
    ('Red 33 Lake', ARRAY['RED', '33', 'LAKE']),
    ('Red 22 Lake', ARRAY['RED', '22', 'LAKE']),
    ('Blue 1 Lake', ARRAY['BLUE', '1', 'LAKE']),
    ('Yellow 5 Lake', ARRAY['YELLOW', '5', 'LAKE']),
    ('Yellow 6 Lake', ARRAY['YELLOW', '6', 'LAKE'])
) AS seed(merged_token, parts)
JOIN product_ingredient_match_terms terms
  ON terms.term = inci_normalize(seed.merged_token);

CREATE TEMP TABLE product_ingredient_sequence_candidates ON COMMIT DROP AS
WITH starts AS (
  SELECT
    pi.id AS keep_id,
    pi.product_id,
    pi.position AS start_position,
    repair.parts,
    repair.merged_token,
    repair.ingredient_id
  FROM product_ingredients pi
  JOIN approved_sequence_repair repair
    ON repair.parts[1] = inci_normalize(pi.raw_inci_token)
),
spans AS (
  SELECT
    starts.keep_id,
    starts.product_id,
    starts.start_position,
    starts.merged_token,
    starts.ingredient_id,
    array_agg(pi.id ORDER BY pi.position) AS ids,
    count(*) AS token_count,
    array_length(starts.parts, 1) AS expected_count
  FROM starts
  JOIN product_ingredients pi
    ON pi.product_id = starts.product_id
   AND pi.position BETWEEN starts.start_position AND starts.start_position + array_length(starts.parts, 1) - 1
   AND inci_normalize(pi.raw_inci_token) = starts.parts[pi.position - starts.start_position + 1]
  GROUP BY starts.keep_id, starts.product_id, starts.start_position, starts.parts, starts.merged_token, starts.ingredient_id
  HAVING count(*) = array_length(starts.parts, 1)
)
SELECT
  *,
  start_position + expected_count - 1 AS end_position
FROM spans
ORDER BY expected_count DESC, product_id, start_position;

DELETE FROM product_ingredient_sequence_candidates later
USING product_ingredient_sequence_candidates earlier
WHERE later.keep_id <> earlier.keep_id
  AND later.product_id = earlier.product_id
  AND later.start_position > earlier.start_position
  AND later.start_position <= earlier.end_position
  AND earlier.expected_count >= later.expected_count;

UPDATE product_ingredients pi
SET raw_inci_token = candidate.merged_token,
    ingredient_id = candidate.ingredient_id,
    is_matched = true
FROM product_ingredient_sequence_candidates candidate
WHERE pi.id = candidate.keep_id;

DELETE FROM product_ingredients pi
USING product_ingredient_sequence_candidates candidate
WHERE pi.id = ANY(candidate.ids[2:array_length(candidate.ids, 1)]);

UPDATE product_ingredients pi
SET ingredient_id = terms.ingredient_id,
    is_matched = true
FROM product_ingredient_match_terms terms
WHERE NOT pi.is_matched
  AND terms.term = inci_normalize(pi.raw_inci_token);

UPDATE product_ingredients pi
SET raw_inci_token = btrim(
      regexp_replace(
        pi.raw_inci_token,
        '^.*\m(?:ingredients?|ngredients?|ingrediants?|inci)\M\s*[:\-]?\s*',
        '',
        'i'
      ),
      ' .:-'
    )
WHERE NOT pi.is_matched
  AND pi.raw_inci_token ~* '\m(?:directions?|instructions?|how\s+to\s+use|usage|uso|warnings?|cautions?|precautions?)\M'
  AND pi.raw_inci_token ~* '\m(?:ingredients?|ngredients?|ingrediants?|inci)\M';

UPDATE product_ingredients pi
SET raw_inci_token = btrim(
      regexp_replace(
        pi.raw_inci_token,
        '\m(?:directions?|instructions?|how\s+to\s+use|usage|uso|warnings?|cautions?|precautions?|for\s+external\s+use\s+only|avoid\s+contact\s+with\s+eyes)\M.*$',
        '',
        'i'
      ),
      ' .:-'
    )
WHERE NOT pi.is_matched
  AND pi.raw_inci_token ~* '\m(?:directions?|instructions?|how\s+to\s+use|usage|uso|warnings?|cautions?|precautions?|for\s+external\s+use\s+only|avoid\s+contact\s+with\s+eyes)\M';

UPDATE product_ingredients pi
SET ingredient_id = terms.ingredient_id,
    is_matched = true
FROM product_ingredient_match_terms terms
WHERE NOT pi.is_matched
  AND terms.term = inci_normalize(pi.raw_inci_token);

DELETE FROM product_ingredients
WHERE NOT is_matched
  AND (
    btrim(raw_inci_token) = ''
    OR inci_normalize(raw_inci_token) IN (
      'absorbed use daily',
      'attention to the wrinkles',
      'directions',
      'directions apply a sufficient amount of',
      'lotion onto cleansed face',
      'neck and',
      'paying special',
      'until fully',
      'upward circular motions'
    )
    OR raw_inci_token ~* '^\s*(lot|batch|mfg|manufacturing|exp|expiry)(\s|$)'
    OR raw_inci_token ~* '\m(?:apply|applying|massage|massaging|massaggia|assorbimento|cleansed|rinse|rinsing|brush|toothbrush|shake before|underarms?|bedtime|sunburn alert|poison control|avoid contact|external use|do not ingest|do not apply|keep out of reach|store at|supervise children|wet hair|damp hair|use daily|use on the body|contact occurs)\M'
    OR (
      array_length(regexp_split_to_array(btrim(raw_inci_token), '\s+'), 1) >= 3
      AND raw_inci_token ~* '\m(?:face|neck|hands?|wrinkles?|circular motions?|skin using|fully absorbed|morning and evening)\M'
    )
  );

DELETE FROM product_ingredients
WHERE NOT is_matched
  AND upper(btrim(raw_inci_token)) IN (
    'ACID',
    'ACRYLATE',
    'ALKYL',
    'BLUE',
    'CROSSPOLYMER',
    'COPOLYMER',
    'CONTAIN',
    'DULCIS',
    'GLYCERYL',
    'GREEN',
    'HYDROGENATED',
    'HYDROLYZED',
    'LAKE',
    'METHOXYPHENYL',
    'NANO',
    'OXIDES',
    'PENTAERYTHRITYL',
    'PROTEIN',
    'RED',
    'STEARATE',
    'SULFATE',
    'TETRA-DI-T-BUTYL',
    'TRIAZINE',
    'YELLOW'
  );

CREATE TEMP TABLE product_ingredient_final_renumber ON COMMIT DROP AS
SELECT
  id,
  row_number() OVER (PARTITION BY product_id ORDER BY position, id)::int AS new_position
FROM product_ingredients;

UPDATE product_ingredients pi
SET position = -renumber.new_position
FROM product_ingredient_final_renumber renumber
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
