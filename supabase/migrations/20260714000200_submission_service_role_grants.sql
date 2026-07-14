-- Supabase no longer auto-exposes newly created tables. Grant only the table
-- privileges used by the submission worker and private curator server.
GRANT SELECT ON ingredients, ingredient_aliases, products, brands,
  product_ingredients TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON product_submissions,
  submission_tokens, submission_audit TO service_role;
