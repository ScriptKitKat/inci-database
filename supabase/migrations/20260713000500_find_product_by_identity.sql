-- Brand + product-name existence check for intake.
--
-- The formula matcher only surfaces products whose formula is exact or
-- >= the similarity threshold, so a same-name product with a diverged
-- formula (reformulation, tokenizer noise) was invisible and apply would
-- create a second product row with the same identity. Intake calls this
-- before verification and routes hits to pending_human. Comparisons
-- mirror find_product_formula_match exactly: case-insensitive trimmed
-- brand, whitespace-collapsed inci_normalize product name.

CREATE OR REPLACE FUNCTION find_product_by_identity(
  p_brand_name TEXT,
  p_product_name TEXT
)
RETURNS TABLE (
  product_id UUID,
  product_name TEXT
)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  SELECT p.id, p.name
  FROM products p
  JOIN brands b ON b.id = p.brand_id
  WHERE upper(trim(b.name)) = upper(trim(p_brand_name))
    AND regexp_replace(inci_normalize(trim(p.name)), '[[:space:]]+', ' ', 'g')
        = regexp_replace(inci_normalize(trim(p_product_name)), '[[:space:]]+', ' ', 'g')
  ORDER BY p.id
  LIMIT 1;
$$;

REVOKE EXECUTE ON FUNCTION find_product_by_identity(TEXT, TEXT)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION find_product_by_identity(TEXT, TEXT)
  TO service_role;
