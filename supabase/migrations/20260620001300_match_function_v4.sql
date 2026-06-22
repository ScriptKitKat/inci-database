-- match_ingredient v4: explicit similarity threshold in the WHERE
-- clause, no dependency on pg_trgm.similarity_threshold.
--
-- Why: hosted Supabase denies non-superuser roles permission to set
-- pg_trgm.similarity_threshold (whether via ALTER DATABASE, function
-- SET clause, or set_limit()). v1's database-level override of the
-- threshold to 0.6 may have been silently rejected, but even if it
-- landed, the % operator's behaviour now depends on a parameter we
-- can't reliably configure. Inlining `similarity() > 0.3` in WHERE
-- removes the implicit dependency.
--
-- Tradeoff: the GIN trigram index can't accelerate this WHERE clause
-- alone, so each fuzzy branch does a sequential scan. At the current
-- 22k ingredients + 8k aliases that's sub-100ms. If the alias table
-- grows past a few hundred thousand rows after PubChem + OBF dump
-- enrichment, revisit by adding `% norm` alongside the similarity
-- check so the index does the prefiltering and similarity() the
-- precise scoring.

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
    SELECT m.ing_id, m.match_type, m.sim
    FROM (
      SELECT i.id           AS ing_id,
             'canonical_fuzzy'::TEXT AS match_type,
             similarity(i.normalized_name, norm) AS sim
      FROM ingredients i
      WHERE similarity(i.normalized_name, norm) > 0.3
      UNION ALL
      SELECT a.ingredient_id AS ing_id,
             'alias_fuzzy'::TEXT AS match_type,
             similarity(a.normalized_alias, norm) AS sim
      FROM ingredient_aliases a
      WHERE similarity(a.normalized_alias, norm) > 0.3
    ) m
    ORDER BY m.sim DESC
    LIMIT 1;
END;
$$;
