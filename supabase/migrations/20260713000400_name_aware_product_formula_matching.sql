-- Make formula matching product-identity aware.
--
-- Exact canonical formulas are automatic duplicates only for the same normalized
-- brand and product name. A close formula is merely a review candidate, and only
-- when its product name differs from the submitted name.
DROP FUNCTION find_product_formula_match(TEXT[], REAL);

CREATE OR REPLACE FUNCTION find_product_formula_match(
  p_tokens TEXT[],
  p_brand_name TEXT,
  p_product_name TEXT,
  p_similarity_threshold REAL DEFAULT 0.95
)
RETURNS TABLE (
  product_id UUID,
  product_name TEXT,
  similarity REAL,
  is_exact BOOLEAN,
  product_name_matches BOOLEAN,
  brand_name_matches BOOLEAN,
  same_product BOOLEAN
)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  WITH input_tokens AS (
    SELECT
      token.ordinality::INTEGER AS position,
      inci_normalize(token.value) AS normalized_token
    FROM unnest(p_tokens) WITH ORDINALITY AS token(value, ordinality)
    WHERE nullif(inci_normalize(token.value), '') IS NOT NULL
  ),
  candidates AS (
    SELECT it.position, i.id AS ingredient_id
    FROM input_tokens it
    JOIN ingredients i ON i.normalized_name = it.normalized_token
    UNION
    SELECT it.position, a.ingredient_id
    FROM input_tokens it
    JOIN ingredient_aliases a ON a.normalized_alias = it.normalized_token
  ),
  resolved_input AS (
    SELECT
      it.position,
      CASE
        WHEN count(DISTINCT c.ingredient_id) = 1
        THEN (array_agg(DISTINCT c.ingredient_id))[1]
      END AS ingredient_id
    FROM input_tokens it
    LEFT JOIN candidates c ON c.position = it.position
    GROUP BY it.position
  ),
  input_formula AS (
    SELECT
      array_agg(ingredient_id ORDER BY position) AS ingredient_ids,
      bool_and(ingredient_id IS NOT NULL) AS all_resolved
    FROM resolved_input
  ),
  input_counts AS (
    SELECT ingredient_id, count(*) AS token_count
    FROM resolved_input
    WHERE ingredient_id IS NOT NULL
    GROUP BY ingredient_id
  ),
  catalog_formulas AS (
    SELECT
      pi.product_id,
      array_agg(pi.ingredient_id ORDER BY pi.position) AS ingredient_ids,
      bool_and(pi.ingredient_id IS NOT NULL) AS all_resolved
    FROM product_ingredients pi
    GROUP BY pi.product_id
  ),
  catalog_counts AS (
    SELECT product_id, ingredient_id, count(*) AS token_count
    FROM product_ingredients
    WHERE ingredient_id IS NOT NULL
    GROUP BY product_id, ingredient_id
  ),
  token_overlaps AS (
    SELECT
      cc.product_id,
      sum(least(cc.token_count, ic.token_count)) AS matching_tokens
    FROM catalog_counts cc
    JOIN input_counts ic USING (ingredient_id)
    GROUP BY cc.product_id
  ),
  scores AS (
    SELECT
      cf.product_id,
      p.name AS product_name,
      (
        coalesce(o.matching_tokens, 0)::REAL
        / greatest(cardinality(cf.ingredient_ids), cardinality(inf.ingredient_ids))
      )::REAL AS similarity,
      (
        inf.all_resolved
        AND cf.all_resolved
        AND cf.ingredient_ids = inf.ingredient_ids
      ) AS is_exact,
      (
        regexp_replace(inci_normalize(trim(p.name)), '[[:space:]]+', ' ', 'g')
        = regexp_replace(inci_normalize(trim(p_product_name)), '[[:space:]]+', ' ', 'g')
      ) AS product_name_matches,
      (upper(trim(b.name)) = upper(trim(p_brand_name))) AS brand_name_matches
    FROM catalog_formulas cf
    JOIN products p ON p.id = cf.product_id
    JOIN brands b ON b.id = p.brand_id
    CROSS JOIN input_formula inf
    LEFT JOIN token_overlaps o ON o.product_id = cf.product_id
    WHERE cardinality(inf.ingredient_ids) > 0
  ),
  classified AS (
    SELECT
      scores.*,
      (scores.product_name_matches AND scores.brand_name_matches) AS same_product
    FROM scores
  )
  SELECT
    classified.product_id,
    classified.product_name,
    classified.similarity,
    classified.is_exact,
    classified.product_name_matches,
    classified.brand_name_matches,
    classified.same_product
  FROM classified
  WHERE classified.is_exact
     OR classified.similarity >= greatest(0.0, least(p_similarity_threshold, 1.0))
  ORDER BY
    (classified.is_exact AND classified.same_product) DESC,
    classified.is_exact DESC,
    (NOT classified.product_name_matches) DESC,
    classified.similarity DESC,
    classified.product_id
  LIMIT 1;
$$;

REVOKE EXECUTE ON FUNCTION find_product_formula_match(TEXT[], TEXT, TEXT, REAL)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION find_product_formula_match(TEXT[], TEXT, TEXT, REAL)
  TO service_role;

-- Keep the transactional race check aligned with intake: formula identity alone
-- cannot collapse a distinct catalog product.
CREATE OR REPLACE FUNCTION apply_product_submission(
  p_id    UUID,
  p_actor TEXT DEFAULT NULL
)
RETURNS TEXT
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  s              product_submissions%ROWTYPE;
  v_actor        TEXT;
  v_formula_ingredient_ids UUID[];
  v_formula_lock TEXT;
  v_existing     UUID;
  v_brand_id     UUID;
  v_brand_norm   TEXT;
  v_brand_slug   TEXT;
  v_product_id   UUID := gen_random_uuid();
  v_product_slug TEXT;
  v_ingredient   UUID;
  v_slug         TEXT;
  v_position     INTEGER := 0;
  v_was_created  BOOLEAN;
  v_cosing       JSONB;
  t              RECORD;
BEGIN
  PERFORM assert_curator_or_service();
  v_actor := coalesce(p_actor, auth.uid()::text, 'service');

  SELECT * INTO s FROM product_submissions WHERE id = p_id FOR UPDATE;
  IF s.id IS NULL THEN
    RAISE EXCEPTION 'submission % not found', p_id;
  END IF;
  IF s.status NOT IN ('decision_ready', 'pending_human') THEN
    RAISE EXCEPTION 'submission % is not apply-eligible: %', p_id, s.status;
  END IF;
  IF EXISTS (
    SELECT 1 FROM submission_tokens
    WHERE submission_id = p_id
      AND resolution IN ('unresolved', 'pending_human', 'unmatched_keep')
  ) THEN
    RAISE EXCEPTION 'submission % has unresolved tokens', p_id;
  END IF;
  IF EXISTS (
    SELECT 1 FROM submission_tokens
    WHERE submission_id = p_id
      AND resolution = 'matched'
      AND matched_ingredient_id IS NULL
  ) THEN
    RAISE EXCEPTION 'submission % has a matched token without an ingredient', p_id;
  END IF;
  IF EXISTS (
    SELECT 1 FROM submission_tokens
    WHERE submission_id = p_id
      AND resolution = 'new_ingredient'
      AND nullif(trim(canonical_name), '') IS NULL
  ) THEN
    RAISE EXCEPTION 'submission % has a new ingredient without a canonical name', p_id;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM submission_tokens
    WHERE submission_id = p_id AND resolution <> 'junk'
  ) THEN
    UPDATE product_submissions
    SET status = 'pending_human', locked_at = NULL
    WHERE id = p_id;
    INSERT INTO submission_audit (submission_id, action, actor, payload)
    VALUES (p_id, 'pending_human', v_actor,
            jsonb_build_object('trigger', 'all_tokens_junk'));
    RETURN 'pending_human';
  END IF;

  -- Compare resolved ingredient IDs directly with existing product formulas.
  SELECT
    array_agg(matched_ingredient_id ORDER BY position),
    string_agg(
      coalesce(
        matched_ingredient_id::TEXT,
        'new:' || inci_normalize(coalesce(canonical_name, raw_token))
      ),
      '|' ORDER BY position
    )
  INTO v_formula_ingredient_ids, v_formula_lock
  FROM submission_tokens
  WHERE submission_id = p_id AND resolution <> 'junk';

  -- The normalized formula is only a transient lock key. Nothing is stored.
  PERFORM pg_advisory_xact_lock(hashtext(v_formula_lock));

  IF array_position(v_formula_ingredient_ids, NULL) IS NULL THEN
    SELECT formula.product_id INTO v_existing
    FROM (
      SELECT
        pi.product_id,
        array_agg(pi.ingredient_id ORDER BY pi.position) AS ingredient_ids,
        bool_and(pi.ingredient_id IS NOT NULL) AS all_resolved
      FROM product_ingredients pi
      GROUP BY pi.product_id
    ) AS formula
    JOIN products p ON p.id = formula.product_id
    JOIN brands b ON b.id = p.brand_id
    WHERE formula.all_resolved
      AND formula.ingredient_ids = v_formula_ingredient_ids
      AND regexp_replace(inci_normalize(trim(p.name)), '[[:space:]]+', ' ', 'g')
          = regexp_replace(inci_normalize(trim(s.product_name)), '[[:space:]]+', ' ', 'g')
      AND upper(trim(b.name)) = upper(trim(s.brand_name))
    ORDER BY formula.product_id
    LIMIT 1;
  END IF;
  IF v_existing IS NOT NULL THEN
    UPDATE product_submissions
    SET status = 'duplicate', product_id = v_existing,
        processed_at = now(), locked_at = NULL
    WHERE id = p_id;
    INSERT INTO submission_audit (submission_id, action, actor, payload)
    VALUES (p_id, 'duplicate', v_actor,
            jsonb_build_object('existing_product_id', v_existing));
    RETURN 'duplicate';
  END IF;

  -- Brand upsert (normalized is a stored generated column: upper(trim(name))).
  v_brand_norm := upper(trim(s.brand_name));
  SELECT b.id INTO v_brand_id FROM brands b WHERE b.normalized = v_brand_norm;
  IF v_brand_id IS NULL THEN
    v_brand_slug := regexp_replace(
      regexp_replace(lower(trim(s.brand_name)), '[^a-z0-9]+', '-', 'g'),
      '(^-|-$)', '', 'g');
    IF v_brand_slug = '' OR EXISTS (SELECT 1 FROM brands WHERE slug = v_brand_slug) THEN
      v_brand_slug := coalesce(nullif(v_brand_slug, ''), 'brand')
        || '-' || left(md5(v_brand_norm), 6);
    END IF;
    INSERT INTO brands (name, slug)
    VALUES (trim(s.brand_name), v_brand_slug)
    ON CONFLICT (normalized) DO NOTHING;
    SELECT b.id INTO v_brand_id FROM brands b WHERE b.normalized = v_brand_norm;
  END IF;

  -- Create new ingredients. Spelling comes exclusively from canonical_name
  -- (an exact authoritative-source string, or curator input).
  FOR t IN
    SELECT * FROM submission_tokens
    WHERE submission_id = p_id AND resolution = 'new_ingredient'
    ORDER BY position
  LOOP
    v_was_created := false;
    v_cosing := '{}'::jsonb;
    PERFORM pg_advisory_xact_lock(
      hashtext('ingredient:' || inci_normalize(t.canonical_name))
    );
    SELECT i.id INTO v_ingredient
    FROM ingredients i
    WHERE i.normalized_name = inci_normalize(t.canonical_name);

    IF v_ingredient IS NULL THEN
      v_slug := regexp_replace(
        regexp_replace(lower(trim(t.canonical_name)), '[^a-z0-9]+', '-', 'g'),
        '(^-|-$)', '', 'g');
      IF v_slug = '' OR EXISTS (SELECT 1 FROM ingredients WHERE slug = v_slug) THEN
        v_slug := coalesce(nullif(v_slug, ''), 'ingredient')
          || '-' || left(md5(t.canonical_name), 6);
      END IF;
      INSERT INTO ingredients (inci_name, slug)
      VALUES (trim(t.canonical_name), v_slug)
      RETURNING id INTO v_ingredient;
      v_was_created := true;
    END IF;

    IF v_was_created THEN
      SELECT coalesce(e.value -> 'enrichment', '{}'::jsonb)
      INTO v_cosing
      FROM jsonb_array_elements(t.evidence) WITH ORDINALITY AS e(value, ordinal)
      WHERE e.value ->> 'source' = 'cosing'
        AND coalesce((e.value ->> 'found')::boolean, false)
      ORDER BY e.ordinal
      LIMIT 1;

      UPDATE ingredient_information
      SET cosing_information = cosing_information || coalesce(v_cosing, '{}'::jsonb),
          updated_at = now()
      WHERE ingredient_id = v_ingredient;

      INSERT INTO ingredient_writeups (ingredient_id, editorial_metadata)
      VALUES (v_ingredient, '{"status":"draft"}'::jsonb)
      ON CONFLICT (ingredient_id) DO NOTHING;

      INSERT INTO ingredient_enrichment_queue (ingredient_id)
      VALUES (v_ingredient)
      ON CONFLICT (ingredient_id) DO NOTHING;
    END IF;

    UPDATE submission_tokens
    SET matched_ingredient_id = v_ingredient, resolution = 'matched'
    WHERE id = t.id;

    IF inci_normalize(t.raw_token) <> inci_normalize(t.canonical_name) THEN
      INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
      VALUES (v_ingredient, t.raw_token, 'synonym', 'en', 'user_submission')
      ON CONFLICT (ingredient_id, alias, language) DO NOTHING;
    END IF;
  END LOOP;

  -- Record confirmed variants as aliases so future submissions hit alias_exact.
  FOR t IN
    SELECT st.*, i.normalized_name AS ingredient_norm
    FROM submission_tokens st
    JOIN ingredients i ON i.id = st.matched_ingredient_id
    WHERE st.submission_id = p_id
      AND st.resolution = 'matched'
      AND st.canonical_name IS NULL
      AND st.resolution_source IN ('deterministic', 'llm', 'human')
  LOOP
    IF inci_normalize(t.raw_token) <> t.ingredient_norm THEN
      INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
      VALUES (
        t.matched_ingredient_id,
        t.raw_token,
        CASE WHEN t.match_type IN ('canonical_fuzzy', 'alias_fuzzy')
             THEN 'typo' ELSE 'synonym' END::alias_type,
        'en',
        'user_submission'
      )
      ON CONFLICT (ingredient_id, alias, language) DO NOTHING;
    END IF;
  END LOOP;

  -- Product.
  v_product_slug := regexp_replace(
    regexp_replace(
      lower(trim(s.brand_name) || '-' || trim(s.product_name)
            || '-' || left(v_product_id::text, 8)),
      '[^a-z0-9]+', '-', 'g'),
    '(^-|-$)', '', 'g');

  INSERT INTO products (id, name, slug, brand_id)
  VALUES (v_product_id, trim(s.product_name), v_product_slug, v_brand_id);

  FOR t IN
    SELECT * FROM submission_tokens
    WHERE submission_id = p_id AND resolution <> 'junk'
    ORDER BY position
  LOOP
    v_position := v_position + 1;
    INSERT INTO product_ingredients (product_id, position, ingredient_id)
    VALUES (v_product_id, v_position, t.matched_ingredient_id);
  END LOOP;

  -- Finalize: drop heavy JSONB, keep lean provenance.
  UPDATE product_submissions
  SET status = 'approved',
      product_id = v_product_id,
      verification = verification - 'online_tokens',
      reviewed_by = auth.uid(),
      reviewed_at = now(),
      processed_at = now(),
      locked_at = NULL
  WHERE id = p_id;

  UPDATE submission_tokens
  SET evidence = '[]'::jsonb
  WHERE submission_id = p_id;

  INSERT INTO submission_audit (submission_id, action, actor, payload)
  VALUES (p_id, 'approve', v_actor,
          jsonb_build_object('product_id', v_product_id, 'brand_id', v_brand_id));

  RETURN 'approved';
END;
$$;
