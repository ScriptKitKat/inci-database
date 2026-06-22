-- Row-Level Security. Public read on ingredients, aliases, products,
-- and published content. ingestion_runs and ingredient_sources stay
-- private (no public-read policy). Writes always go through the
-- service role, which bypasses RLS.

ALTER TABLE ingredients          ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_aliases   ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_content   ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_sources   ENABLE ROW LEVEL SECURITY;
ALTER TABLE products             ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_ingredients  ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_runs       ENABLE ROW LEVEL SECURITY;

CREATE POLICY public_read_ingredients ON ingredients
  FOR SELECT USING (true);

CREATE POLICY public_read_aliases ON ingredient_aliases
  FOR SELECT USING (true);

CREATE POLICY public_read_published_content ON ingredient_content
  FOR SELECT USING (status = 'published');

CREATE POLICY public_read_products ON products
  FOR SELECT USING (true);

CREATE POLICY public_read_product_ingredients ON product_ingredients
  FOR SELECT USING (true);
