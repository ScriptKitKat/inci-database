-- Add 'wikidata' to the source_type enum so SPARQL-enriched provenance
-- rows can be persisted in ingredient_sources without using the
-- catch-all 'manual' value.

ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'wikidata';
