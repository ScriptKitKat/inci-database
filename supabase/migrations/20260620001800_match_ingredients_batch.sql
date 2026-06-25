-- Batch wrapper around match_ingredient for bulk product ingestion.
-- One HTTP round-trip resolves many tokens; logic stays identical to v4.

CREATE OR REPLACE FUNCTION match_ingredients_batch(inputs TEXT[])
RETURNS TABLE (
  input_token   TEXT,
  ingredient_id UUID,
  match_type    TEXT,
  confidence    REAL
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  tok TEXT;
BEGIN
  IF inputs IS NULL OR array_length(inputs, 1) IS NULL THEN
    RETURN;
  END IF;

  FOREACH tok IN ARRAY inputs LOOP
    IF tok IS NULL OR btrim(tok) = '' THEN
      CONTINUE;
    END IF;

    RETURN QUERY
      SELECT tok, m.ingredient_id, m.match_type, m.confidence
      FROM match_ingredient(tok) AS m;
  END LOOP;
END;
$$;
