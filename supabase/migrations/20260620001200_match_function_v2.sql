-- match_ingredient v2: fuzzy match against canonical names in
-- addition to aliases. The v1 cascade only trigram-matched against
-- ingredient_aliases, which means a typo lookup ('salycilic acid')
-- could not find an ingredient whose alias table was empty -- which
-- is most of them right after stage 1 since the OBF taxonomy carries
-- few synonyms.
--
-- New cascade:
--   1. canonical exact   (similarity 1.00)
--   2. alias     exact   (similarity 0.98)
--   3. union of canonical + alias trigram fuzzy, pick the best

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
      WHERE i.normalized_name % norm
      UNION ALL
      SELECT a.ingredient_id AS ing_id,
             'alias_fuzzy'::TEXT AS match_type,
             similarity(a.normalized_alias, norm) AS sim
      FROM ingredient_aliases a
      WHERE a.normalized_alias % norm
    ) m
    ORDER BY m.sim DESC
    LIMIT 1;
END;
$$;
