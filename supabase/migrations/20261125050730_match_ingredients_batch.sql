-- Keep tokens in request order and omit unmatched inputs so API clients can
-- distinguish missing results without decoding nullable match fields.
CREATE OR REPLACE FUNCTION public.match_ingredients_batch(inputs TEXT[])
RETURNS TABLE (input_token TEXT, ingredient_id UUID, match_type TEXT, confidence REAL)
LANGUAGE sql STABLE
SET search_path = public
AS $$
  SELECT requested.token, matched.ingredient_id, matched.match_type, matched.confidence
  FROM unnest(inputs) WITH ORDINALITY AS requested(token, ord)
  CROSS JOIN LATERAL public.match_ingredient(requested.token) AS matched
  WHERE public.inci_normalize(requested.token) <> ''
  ORDER BY requested.ord;
$$;

REVOKE EXECUTE ON FUNCTION public.match_ingredients_batch(TEXT[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.match_ingredients_batch(TEXT[]) TO anon, authenticated, service_role;
