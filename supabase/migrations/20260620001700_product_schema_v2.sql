-- Replace the interim product schema (20260620000600) with the MVP
-- product database design: brands, products, product_ingredients.
--
-- Barcodes, images, and categories are intentionally deferred.
-- See product database design doc for rationale.

CREATE TYPE product_status AS ENUM ('pending', 'approved', 'rejected');

-- Drop interim tables. Any rows from the old import are discarded;
-- re-seed with the products pipeline stage after this migration.
DROP TABLE IF EXISTS product_ingredients;
DROP TABLE IF EXISTS products;

-- ---------------------------------------------------------------------------
-- brands
-- ---------------------------------------------------------------------------

CREATE TABLE brands (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  slug        TEXT NOT NULL UNIQUE,
  normalized  TEXT GENERATED ALWAYS AS (upper(trim(name))) STORED,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (normalized)
);

CREATE INDEX idx_brands_trigram ON brands USING gin (name gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- products
-- ---------------------------------------------------------------------------

CREATE TABLE products (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                   TEXT NOT NULL,
  slug                   TEXT NOT NULL UNIQUE,
  brand_id               UUID NOT NULL REFERENCES brands(id),

  short_description      TEXT,
  ingredient_fingerprint TEXT,

  status                 product_status NOT NULL DEFAULT 'approved',
  search_vector          TSVECTOR,

  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_products_brand_id ON products (brand_id);
CREATE INDEX idx_products_search ON products USING gin (search_vector);
CREATE INDEX idx_products_name_trigram ON products USING gin (name gin_trgm_ops);

CREATE UNIQUE INDEX idx_products_fingerprint
  ON products (ingredient_fingerprint)
  WHERE ingredient_fingerprint IS NOT NULL;

-- ---------------------------------------------------------------------------
-- product_ingredients
-- ---------------------------------------------------------------------------

CREATE TABLE product_ingredients (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id      UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  ingredient_id   UUID REFERENCES ingredients(id) ON DELETE SET NULL,

  position        INTEGER NOT NULL,
  raw_inci_token  TEXT NOT NULL,
  is_matched      BOOLEAN NOT NULL DEFAULT false,

  UNIQUE (product_id, position)
);

CREATE INDEX idx_pi_product_id ON product_ingredients (product_id);
CREATE INDEX idx_pi_ingredient_id ON product_ingredients (ingredient_id);

-- ---------------------------------------------------------------------------
-- full-text search vector (name > brand > description)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(
      (SELECT b.name FROM brands b WHERE b.id = NEW.brand_id), ''
    )), 'B') ||
    setweight(to_tsvector('english', coalesce(NEW.short_description, '')), 'C');
  RETURN NEW;
END;
$$;

CREATE TRIGGER trig_product_search_vector
  BEFORE INSERT OR UPDATE ON products
  FOR EACH ROW
  EXECUTE FUNCTION update_product_search_vector();

CREATE TRIGGER trg_products_updated
  BEFORE UPDATE ON products
  FOR EACH ROW
  EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- RLS (re-enable on recreated tables; policies from 009 were dropped with the
-- interim tables)
-- ---------------------------------------------------------------------------

ALTER TABLE brands ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_ingredients ENABLE ROW LEVEL SECURITY;

CREATE POLICY public_read_brands ON brands
  FOR SELECT USING (true);

CREATE POLICY public_read_products ON products
  FOR SELECT USING (status = 'approved');

CREATE POLICY public_read_product_ingredients ON product_ingredients
  FOR SELECT USING (
    EXISTS (
      SELECT 1
      FROM products p
      WHERE p.id = product_ingredients.product_id
        AND p.status = 'approved'
    )
  );
