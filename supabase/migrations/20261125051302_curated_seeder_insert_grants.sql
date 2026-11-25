-- The curated seeder writes catalog rows directly rather than through the
-- submission approval RPC. Grant only the columns it supplies on insert.
GRANT INSERT (name, slug) ON public.brands TO service_role;
GRANT INSERT (name, slug, brand_id, short_description) ON public.products TO service_role;
GRANT INSERT (product_id, ingredient_id, position) ON public.product_ingredients TO service_role;
