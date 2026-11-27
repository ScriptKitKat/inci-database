DO $$
DECLARE
  v_labels TEXT[];
BEGIN
  SELECT array_agg(enumlabel::TEXT ORDER BY enumsortorder)
  INTO v_labels
  FROM pg_enum
  WHERE enumtypid = 'public.ingredient_rating'::regtype;

  IF v_labels = ARRAY['ew_ew', 'okie', 'yippe', 'wowza'] THEN
    RETURN;
  END IF;

  IF v_labels IS DISTINCT FROM ARRAY['superhero', 'great', 'average', 'not_good', 'bad'] THEN
    RAISE EXCEPTION 'Unexpected ingredient_rating values: %', v_labels;
  END IF;

  ALTER TYPE public.ingredient_rating RENAME TO ingredient_rating_legacy;
  CREATE TYPE public.ingredient_rating AS ENUM ('ew_ew', 'okie', 'yippe', 'wowza');

  ALTER TABLE public.ingredient_information
    ALTER COLUMN rating TYPE public.ingredient_rating
    USING (
      CASE rating::TEXT
        WHEN 'superhero' THEN 'wowza'
        WHEN 'great' THEN 'yippe'
        WHEN 'average' THEN 'okie'
        WHEN 'not_good' THEN 'ew_ew'
        WHEN 'bad' THEN 'ew_ew'
      END
    )::public.ingredient_rating;

  DROP TYPE public.ingredient_rating_legacy;
END;
$$;
