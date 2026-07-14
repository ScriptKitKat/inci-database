BEGIN;

SET LOCAL statement_timeout = '15min';

CREATE TEMP TABLE today_nonplant_ingredient_candidates ON COMMIT DROP AS
SELECT i.id
FROM ingredients i
WHERE i.created_at >= timestamptz '2026-06-30 00:00:00 America/New_York'
  AND i.created_at <  timestamptz '2026-07-01 00:00:00 America/New_York'
  AND i.inci_name !~* '(extract|oil|flower|plant|botanic|botanical|herb|leaf|leaves|root|seed|fruit|bark|peel|rind|juice|sap|stem|branch|wood|bud|gum|resin|wax|butter|kernel|nut|berry|algae|seaweed|kelp|ferment|mushroom|fungus|lichen|citrus|rosa|camellia|aloe|helianthus|butyrospermum|simmondsia|cocos|argania|opuntia|olea|glycine|max|prunus|vitis|lavandula|centella|calendula|chamomilla|cucumis|cucurbita|oryza|avena|triticum|zea|punica|moringa|eucalyptus|mentha|melaleuca|cinnamomum)';

CREATE TABLE IF NOT EXISTS ingredient_cleanup_backup_20260630_nonplant (
  backed_up_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ingredient JSONB NOT NULL,
  aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
  product_ingredient_refs JSONB NOT NULL DEFAULT '[]'::jsonb
);

INSERT INTO ingredient_cleanup_backup_20260630_nonplant (
  ingredient,
  aliases,
  product_ingredient_refs
)
SELECT
  to_jsonb(i) AS ingredient,
  coalesce(alias_rows.aliases, '[]'::jsonb) AS aliases,
  coalesce(product_rows.product_ingredient_refs, '[]'::jsonb) AS product_ingredient_refs
FROM ingredients i
JOIN today_nonplant_ingredient_candidates c
  ON c.id = i.id
LEFT JOIN LATERAL (
  SELECT jsonb_agg(to_jsonb(a) ORDER BY a.alias) AS aliases
  FROM ingredient_aliases a
  WHERE a.ingredient_id = i.id
) alias_rows ON true
LEFT JOIN LATERAL (
  SELECT jsonb_agg(to_jsonb(pi) ORDER BY pi.product_id, pi.position, pi.id) AS product_ingredient_refs
  FROM product_ingredients pi
  WHERE pi.ingredient_id = i.id
) product_rows ON true
WHERE NOT EXISTS (
  SELECT 1
  FROM ingredient_cleanup_backup_20260630_nonplant b
  WHERE (b.ingredient ->> 'id')::uuid = i.id
);

UPDATE product_ingredients pi
SET ingredient_id = NULL,
    is_matched = false
FROM today_nonplant_ingredient_candidates c
WHERE pi.ingredient_id = c.id;

DELETE FROM ingredient_aliases a
USING today_nonplant_ingredient_candidates c
WHERE a.ingredient_id = c.id;

DELETE FROM ingredients i
USING today_nonplant_ingredient_candidates c
WHERE i.id = c.id;

COMMIT;
