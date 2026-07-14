INSERT INTO brand_product_domains (normalized_brand_name, domain)
VALUES ('GLOW RECIPE', 'glowrecipe.com')
ON CONFLICT (normalized_brand_name, domain) DO NOTHING;
