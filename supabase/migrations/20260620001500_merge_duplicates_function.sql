-- Reusable admin utility for collapsing duplicate ingredient rows.
-- See Welcome.md for the user-facing explanation.
--
-- Strategy:
--   * Winner is the row with the most aliases (created_at tiebreak).
--   * Scalar metadata is promoted onto the winner where the winner is NULL.
--   * Aliases, sources, products, curation entries, and editorial content
--     are migrated from losers to the winner with ON CONFLICT dedup.
--   * Loser inci_names themselves become aliases on the winner so the
--     decoder can still resolve labels that used the old spelling.
--   * Losers are deleted; FK CASCADE cleans up anything we missed.
--   * Winner is renamed to (canonical_inci_name, preferred_slug).

CREATE OR REPLACE FUNCTION merge_duplicate_ingredients(
  target_normalized_name TEXT,
  canonical_inci_name    TEXT,
  preferred_slug         TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
  v_winner    UUID;
  v_loser_ids UUID[];
BEGIN
  SELECT i.id INTO v_winner
  FROM ingredients i
  WHERE i.normalized_name = target_normalized_name
  ORDER BY (SELECT count(*) FROM ingredient_aliases a WHERE a.ingredient_id = i.id) DESC,
           i.created_at ASC
  LIMIT 1;

  IF v_winner IS NULL THEN
    RETURN format('no rows with normalized_name=%L found', target_normalized_name);
  END IF;

  SELECT array_agg(id) INTO v_loser_ids
  FROM ingredients
  WHERE normalized_name = target_normalized_name AND id <> v_winner;

  IF array_length(v_loser_ids, 1) IS NULL THEN
    UPDATE ingredients SET inci_name = canonical_inci_name, slug = preferred_slug
    WHERE id = v_winner AND (inci_name <> canonical_inci_name OR slug <> preferred_slug);
    RETURN format('one row exists, normalized to %L', canonical_inci_name);
  END IF;

  UPDATE ingredients w
  SET cas_number = COALESCE(w.cas_number,
        (SELECT l.cas_number FROM ingredients l WHERE l.id = ANY(v_loser_ids) AND l.cas_number IS NOT NULL LIMIT 1)),
      ec_number = COALESCE(w.ec_number,
        (SELECT l.ec_number  FROM ingredients l WHERE l.id = ANY(v_loser_ids) AND l.ec_number  IS NOT NULL LIMIT 1)),
      iupac_name = COALESCE(w.iupac_name,
        (SELECT l.iupac_name FROM ingredients l WHERE l.id = ANY(v_loser_ids) AND l.iupac_name IS NOT NULL LIMIT 1)),
      ph_eur_name = COALESCE(w.ph_eur_name,
        (SELECT l.ph_eur_name FROM ingredients l WHERE l.id = ANY(v_loser_ids) AND l.ph_eur_name IS NOT NULL LIMIT 1))
  WHERE w.id = v_winner;

  INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
  SELECT v_winner, a.alias, a.alias_type, a.language, a.source
  FROM ingredient_aliases a
  WHERE a.ingredient_id = ANY(v_loser_ids)
  ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

  INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
  SELECT v_winner, i.inci_name, 'inci', 'en', 'manual'
  FROM ingredients i
  WHERE i.id = ANY(v_loser_ids)
  ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

  INSERT INTO ingredient_sources (ingredient_id, source_type, external_id, url, title, raw_payload)
  SELECT v_winner, s.source_type, s.external_id, s.url, s.title, s.raw_payload
  FROM ingredient_sources s
  WHERE s.ingredient_id = ANY(v_loser_ids)
  ON CONFLICT (ingredient_id, source_type, external_id) DO NOTHING;

  UPDATE product_ingredients
  SET ingredient_id = v_winner
  WHERE ingredient_id = ANY(v_loser_ids);

  INSERT INTO ingredient_curation_queue (ingredient_id, priority, notes)
  SELECT v_winner, q.priority, q.notes
  FROM ingredient_curation_queue q
  WHERE q.ingredient_id = ANY(v_loser_ids)
  ON CONFLICT (ingredient_id) DO NOTHING;

  INSERT INTO ingredient_content
    (ingredient_id, language, summary_short, summary_long, quick_facts, what_it_does,
     status, model_version, reviewed_by, reviewed_at)
  SELECT v_winner, c.language, c.summary_short, c.summary_long, c.quick_facts, c.what_it_does,
         c.status, c.model_version, c.reviewed_by, c.reviewed_at
  FROM ingredient_content c
  WHERE c.ingredient_id = ANY(v_loser_ids)
  ON CONFLICT (ingredient_id, language) DO NOTHING;

  DELETE FROM ingredients WHERE id = ANY(v_loser_ids);

  UPDATE ingredients
  SET inci_name = canonical_inci_name, slug = preferred_slug
  WHERE id = v_winner;

  RETURN format('merged %s loser(s) into winner %s, canonical=%L',
                array_length(v_loser_ids, 1), v_winner, canonical_inci_name);
END $$;
