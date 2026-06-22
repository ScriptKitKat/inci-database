-- Provenance for every claim. raw_payload preserves the original API
-- response so editorial summaries can be regenerated when an abstract
-- is retracted or a CosIng entry changes.

CREATE TABLE ingredient_sources (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
  source_type   source_type NOT NULL,
  external_id   TEXT,
  url           TEXT,
  title         TEXT,
  raw_payload   JSONB,
  retrieved_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (ingredient_id, source_type, external_id)
);

CREATE INDEX sources_ingredient_idx ON ingredient_sources (ingredient_id);
CREATE INDEX sources_payload_gin    ON ingredient_sources USING GIN (raw_payload);
