-- Aliases power fuzzy matching. Every label variant, synonym, trade
-- name, and translation lives here. `source` tracks provenance so
-- hand-curated aliases can be distinguished from OBF-harvested ones.

CREATE TABLE ingredient_aliases (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_id    UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
  alias            TEXT NOT NULL,
  normalized_alias TEXT GENERATED ALWAYS AS (inci_normalize(alias)) STORED,
  alias_type       alias_type NOT NULL DEFAULT 'synonym',
  language         TEXT NOT NULL DEFAULT 'en',
  source           source_type NOT NULL DEFAULT 'manual',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (ingredient_id, alias, language)
);

CREATE INDEX aliases_normalized_trgm ON ingredient_aliases USING GIN (normalized_alias gin_trgm_ops);
CREATE INDEX aliases_normalized_eq   ON ingredient_aliases (normalized_alias);
CREATE INDEX aliases_ingredient_idx  ON ingredient_aliases (ingredient_id);
