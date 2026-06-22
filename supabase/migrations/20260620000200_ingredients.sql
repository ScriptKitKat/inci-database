-- Master ingredients table. INCI name is the canonical key.
-- normalized_name is a STORED generated column so trigram lookups
-- never depend on the caller having normalized the input.

CREATE TABLE ingredients (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inci_name             TEXT NOT NULL UNIQUE,
  slug                  TEXT NOT NULL UNIQUE,
  normalized_name       TEXT GENERATED ALWAYS AS (inci_normalize(inci_name)) STORED,

  rating                ingredient_rating,
  function_tags         TEXT[] NOT NULL DEFAULT '{}',
  skin_type_tag         TEXT[] NOT NULL DEFAULT '{}',
  concern_tag           TEXT[] NOT NULL DEFAULT '{}',

  cas_number            TEXT,
  ec_number             TEXT,
  iupac_name            TEXT,
  ph_eur_name           TEXT,

  is_restricted_eu      BOOLEAN NOT NULL DEFAULT false,
  is_restricted_us      BOOLEAN NOT NULL DEFAULT false,
  is_comedogenic        BOOLEAN,
  irritancy_level       irritancy_level,

  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ingredients_function_tags_gin ON ingredients USING GIN (function_tags);
CREATE INDEX ingredients_skin_type_tag_gin ON ingredients USING GIN (skin_type_tag);
CREATE INDEX ingredients_concern_tag_gin   ON ingredients USING GIN (concern_tag);
CREATE INDEX ingredients_normalized_trgm   ON ingredients USING GIN (normalized_name gin_trgm_ops);
CREATE INDEX ingredients_cas_number_idx    ON ingredients (cas_number) WHERE cas_number IS NOT NULL;
