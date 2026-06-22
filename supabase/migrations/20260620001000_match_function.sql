-- Shared matching cascade. Used by the eventual decode endpoint and
-- by the OBF alias harvester so there is exactly one matching
-- definition in the system.
--
-- Cascade: canonical exact -> alias exact -> alias trigram fuzzy.
-- Returns at most one row. Never guesses below the trigram threshold.

CREATE OR REPLACE FUNCTION match_ingredient(input TEXT)
RETURNS TABLE (ingredient_id UUID, match_type TEXT, confidence REAL)
LANGUAGE plpgsql STABLE AS $$
DECLARE
  norm TEXT := inci_normalize(input);
BEGIN
  RETURN QUERY
    SELECT i.id, 'canonical_exact'::TEXT, 1.0::REAL
    FROM ingredients i
    WHERE i.normalized_name = norm
    LIMIT 1;
  IF FOUND THEN RETURN; END IF;

  RETURN QUERY
    SELECT a.ingredient_id, 'alias_exact'::TEXT, 0.98::REAL
    FROM ingredient_aliases a
    WHERE a.normalized_alias = norm
    LIMIT 1;
  IF FOUND THEN RETURN; END IF;

  RETURN QUERY
    SELECT a.ingredient_id, 'alias_fuzzy'::TEXT, similarity(a.normalized_alias, norm)
    FROM ingredient_aliases a
    WHERE a.normalized_alias % norm
    ORDER BY similarity(a.normalized_alias, norm) DESC
    LIMIT 1;
END;
$$;

-- Tune trigram similarity threshold. 0.5 is the Postgres default;
-- we raise it slightly to reduce false positives on short tokens.
ALTER DATABASE postgres SET pg_trgm.similarity_threshold = 0.6;
