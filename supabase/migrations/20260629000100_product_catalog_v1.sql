-- Product catalog MVP: brands, lean products, ordered ingredient links,
-- search vectors, and public visibility only for approved products.

CREATE TABLE IF NOT EXISTS brands (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  slug        TEXT NOT NULL UNIQUE,
  normalized  TEXT GENERATED ALWAYS AS (upper(trim(name))) STORED UNIQUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brands_trigram
  ON brands USING gin(name gin_trgm_ops);

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS slug TEXT,
  ADD COLUMN IF NOT EXISTS brand_id UUID REFERENCES brands(id),
  ADD COLUMN IF NOT EXISTS short_description TEXT,
  ADD COLUMN IF NOT EXISTS ingredient_fingerprint TEXT,
  ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'approved'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'products'
      AND column_name = 'brand'
  ) THEN
    INSERT INTO brands (name, slug)
    SELECT DISTINCT
      brand_name,
      COALESCE(NULLIF(brand_slug, ''), 'brand')
        || '-' || left(md5(upper(trim(brand_name))), 6)
    FROM (
      SELECT
        COALESCE(NULLIF(trim(brand), ''), 'Unknown') AS brand_name,
        regexp_replace(
          lower(
            regexp_replace(
              COALESCE(NULLIF(trim(brand), ''), 'Unknown'),
              '[^a-zA-Z0-9]+',
              '-',
              'g'
            )
          ),
          '(^-|-$)',
          '',
          'g'
        ) AS brand_slug
      FROM products
    ) source_brands
    ON CONFLICT (normalized) DO NOTHING;

    UPDATE products p
    SET brand_id = b.id
    FROM brands b
    WHERE p.brand_id IS NULL
      AND b.normalized = upper(trim(COALESCE(NULLIF(p.brand, ''), 'Unknown')));
  END IF;
END $$;

UPDATE products p
SET slug = regexp_replace(
    lower(
      regexp_replace(
        COALESCE(b.name, 'unknown') || '-' || p.name || '-' || left(p.id::text, 8),
        '[^a-zA-Z0-9]+',
        '-',
        'g'
      )
    ),
    '(^-|-$)',
    '',
    'g'
  )
FROM brands b
WHERE p.slug IS NULL
  AND b.id = p.brand_id;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'product_ingredients'
      AND column_name = 'raw_token'
  ) AND NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'product_ingredients'
      AND column_name = 'raw_inci_token'
  ) THEN
    ALTER TABLE product_ingredients RENAME COLUMN raw_token TO raw_inci_token;
  END IF;
END $$;

ALTER TABLE product_ingredients
  ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid(),
  ADD COLUMN IF NOT EXISTS raw_inci_token TEXT,
  ADD COLUMN IF NOT EXISTS is_matched BOOLEAN NOT NULL DEFAULT false;

UPDATE product_ingredients
SET id = gen_random_uuid()
WHERE id IS NULL;

UPDATE product_ingredients
SET is_matched = ingredient_id IS NOT NULL
WHERE is_matched = false
  AND ingredient_id IS NOT NULL;

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
SET ingredient_fingerprint = u.fingerprint
FROM unique_fingerprints u
WHERE p.id = u.product_id
  AND p.ingredient_fingerprint IS NULL
  AND u.duplicate_count = 1;

ALTER TABLE products
  ALTER COLUMN slug SET NOT NULL,
  ALTER COLUMN brand_id SET NOT NULL;

ALTER TABLE product_ingredients
  ALTER COLUMN id SET NOT NULL,
  ALTER COLUMN raw_inci_token SET NOT NULL;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'product_ingredients'::regclass
      AND conname = 'product_ingredients_pkey'
  ) THEN
    ALTER TABLE product_ingredients DROP CONSTRAINT product_ingredients_pkey;
  END IF;
END $$;

ALTER TABLE product_ingredients
  ADD CONSTRAINT product_ingredients_pkey PRIMARY KEY (id);

CREATE UNIQUE INDEX IF NOT EXISTS product_ingredients_product_position_key
  ON product_ingredients (product_id, position);

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_slug
  ON products (slug);

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_fingerprint
  ON products (ingredient_fingerprint)
  WHERE ingredient_fingerprint IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_products_brand_id
  ON products (brand_id);

CREATE INDEX IF NOT EXISTS idx_products_search
  ON products USING gin(search_vector);

CREATE INDEX IF NOT EXISTS idx_products_name_trigram
  ON products USING gin(name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_pi_product_id
  ON product_ingredients (product_id);

CREATE INDEX IF NOT EXISTS idx_pi_ingredient_id
  ON product_ingredients (ingredient_id);

CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(
      (SELECT name FROM brands WHERE id = NEW.brand_id), ''
    )), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.short_description, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trig_product_search_vector ON products;
CREATE TRIGGER trig_product_search_vector
  BEFORE INSERT OR UPDATE ON products
  FOR EACH ROW EXECUTE FUNCTION update_product_search_vector();

CREATE OR REPLACE FUNCTION refresh_product_search_vector_for_brand()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE products
  SET updated_at = updated_at
  WHERE brand_id = NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trig_brand_refresh_product_search_vector ON brands;
CREATE TRIGGER trig_brand_refresh_product_search_vector
  AFTER UPDATE OF name ON brands
  FOR EACH ROW
  WHEN (OLD.name IS DISTINCT FROM NEW.name)
  EXECUTE FUNCTION refresh_product_search_vector_for_brand();

UPDATE products SET updated_at = updated_at;

ALTER TABLE products
  DROP COLUMN IF EXISTS external_id,
  DROP COLUMN IF EXISTS external_source,
  DROP COLUMN IF EXISTS brand,
  DROP COLUMN IF EXISTS raw_ingredients,
  DROP COLUMN IF EXISTS decoded_at;

ALTER TABLE product_ingredients
  DROP COLUMN IF EXISTS match_confidence;

ALTER TABLE brands ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS public_read_brands ON brands;
CREATE POLICY public_read_brands ON brands
  FOR SELECT USING (true);

DROP POLICY IF EXISTS public_read_products ON products;
CREATE POLICY public_read_products ON products
  FOR SELECT USING (status = 'approved');

DROP POLICY IF EXISTS public_read_product_ingredients ON product_ingredients;
CREATE POLICY public_read_product_ingredients ON product_ingredients
  FOR SELECT USING (
    EXISTS (
      SELECT 1
      FROM products p
      WHERE p.id = product_ingredients.product_id
        AND p.status = 'approved'
    )
  );
