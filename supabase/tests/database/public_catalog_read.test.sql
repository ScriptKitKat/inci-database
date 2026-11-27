BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SELECT plan(12);

CREATE FUNCTION pg_temp.reads_as(p_role TEXT, p_table TEXT)
RETURNS SETOF TEXT
LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE format('SET LOCAL ROLE %I', p_role);
  RETURN NEXT lives_ok(format('SELECT 1 FROM public.%I LIMIT 1', p_table),
                       p_role || ' can read ' || p_table);
  RESET ROLE;
END;
$$;

SELECT pg_temp.reads_as(r, t)
FROM unnest(ARRAY['brands', 'products', 'product_ingredients',
                  'ingredients', 'ingredient_aliases', 'ingredient_information']) AS t,
     unnest(ARRAY['anon', 'authenticated']) AS r;

SELECT * FROM finish();
ROLLBACK;
