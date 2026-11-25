CREATE OR REPLACE FUNCTION public.match_ingredients_batch(inputs TEXT[])
RETURNS TABLE (input_token TEXT, ingredient_id UUID, match_type TEXT, confidence REAL)
LANGUAGE plpgsql STABLE
SET search_path = public
AS $$
BEGIN
  IF cardinality(inputs) > 50 THEN
    RAISE EXCEPTION 'match_ingredients_batch accepts at most 50 inputs' USING ERRCODE = '22023';
  END IF;

  RETURN QUERY
    SELECT requested.token, matched.ingredient_id, matched.match_type, matched.confidence
    FROM unnest(inputs) WITH ORDINALITY AS requested(token, ord)
    CROSS JOIN LATERAL public.match_ingredient(requested.token) AS matched
    WHERE public.inci_normalize(requested.token) <> ''
    ORDER BY requested.ord;
END;
$$;
