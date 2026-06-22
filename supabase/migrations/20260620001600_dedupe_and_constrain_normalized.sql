-- Collapse every remaining duplicate normalized_name group, then
-- enforce the constraint going forward so stage 1 re-runs can't
-- reintroduce the bug.
--
-- Auto-merge uses each winner's existing inci_name and slug as
-- canonical -- that is, it never picks a "wrong" canonical, just
-- keeps whichever variant happens to have the most aliases. Curate
-- the canonical name later by calling merge_duplicate_ingredients()
-- again with your preferred inci_name.

DO $$
DECLARE
  dup_norm    TEXT;
  winner_name TEXT;
  winner_slug TEXT;
BEGIN
  FOR dup_norm IN
    SELECT normalized_name
    FROM ingredients
    GROUP BY normalized_name
    HAVING count(*) > 1
  LOOP
    SELECT i.inci_name, i.slug INTO winner_name, winner_slug
    FROM ingredients i
    WHERE i.normalized_name = dup_norm
    ORDER BY (SELECT count(*) FROM ingredient_aliases a WHERE a.ingredient_id = i.id) DESC,
             i.created_at ASC
    LIMIT 1;

    PERFORM merge_duplicate_ingredients(dup_norm, winner_name, winner_slug);
  END LOOP;
END $$;

ALTER TABLE ingredients
  ADD CONSTRAINT ingredients_normalized_name_key UNIQUE (normalized_name);
