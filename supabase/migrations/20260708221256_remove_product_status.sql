-- Remove product moderation status and approval-gated read policies.

DROP POLICY IF EXISTS public_read_product_ingredients ON product_ingredients;
DROP POLICY IF EXISTS public_read_products ON products;

ALTER TABLE products
  DROP COLUMN IF EXISTS status;

CREATE POLICY public_read_products ON products
  FOR SELECT USING (true);

CREATE POLICY public_read_product_ingredients ON product_ingredients
  FOR SELECT USING (true);
