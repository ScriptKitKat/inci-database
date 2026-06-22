-- Postgres extensions required by the schema.
-- pgvector is deferred until semantic search becomes a requirement.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- IMMUTABLE wrapper around unaccent() so it can be used inside
-- GENERATED ... STORED columns and functional indexes. unaccent() is
-- declared STABLE because the dictionary could theoretically change at
-- runtime, but the dictionary-explicit two-argument form is safe to
-- promise immutable. lower() and regexp_replace() are already
-- IMMUTABLE so the composition is too.
CREATE OR REPLACE FUNCTION inci_normalize(input text)
RETURNS text
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
STRICT
AS $$
  SELECT lower(
    public.unaccent('public.unaccent',
      regexp_replace(input, '[^a-zA-Z0-9 ]', '', 'g')
    )
  );
$$;
