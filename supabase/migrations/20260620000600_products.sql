-- Products and their decoded ingredient lists. raw_token is kept on
-- product_ingredients so the UI can always show "label said X -> we
-- matched it to Y" which is critical for user trust.

CREATE TABLE products (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id     TEXT,
  external_source source_type,
  brand           TEXT,
  name            TEXT NOT NULL,
  raw_ingredients TEXT NOT NULL,
  decoded_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (external_source, external_id)
);

CREATE TABLE product_ingredients (
  product_id       UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  position         INTEGER NOT NULL,
  raw_token        TEXT NOT NULL,
  ingredient_id    UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  match_confidence REAL,
  PRIMARY KEY (product_id, position)
);

CREATE INDEX product_ingredients_ingredient_idx ON product_ingredients (ingredient_id);
