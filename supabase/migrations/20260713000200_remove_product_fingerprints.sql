-- Match product formulas directly instead of persisting ingredient fingerprints.

-- Compare queued ingredient lists directly with catalog formulas.
-- No fingerprint or formula hash is persisted.
CREATE OR REPLACE FUNCTION find_product_formula_match(
  p_tokens TEXT[],
  p_similarity_threshold REAL DEFAULT 0.80
)
RETURNS TABLE (
  product_id UUID,
  similarity REAL,
  is_exact BOOLEAN
)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  WITH input_tokens AS (
    SELECT
      token.ordinality::INTEGER AS position,
      inci_normalize(token.value) AS normalized_token
    FROM unnest(p_tokens) WITH ORDINALITY AS token(value, ordinality)
    WHERE nullif(trim(token.value), '') IS NOT NULL
  ),
  input_formula AS (
    SELECT array_agg(normalized_token ORDER BY position) AS tokens
    FROM input_tokens
  ),
  input_counts AS (
    SELECT normalized_token, count(*) AS token_count
    FROM input_tokens
    GROUP BY normalized_token
  ),
  catalog_tokens AS (
    SELECT
      pi.product_id,
      pi.position,
      inci_normalize(
        coalesce(nullif(trim(pim.raw_inci_token), ''), i.inci_name)
      ) AS normalized_token
    FROM product_ingredients pi
    LEFT JOIN product_ingredient_metadata pim
      ON pim.product_ingredient_id = pi.id
    LEFT JOIN ingredients i ON i.id = pi.ingredient_id
    WHERE coalesce(nullif(trim(pim.raw_inci_token), ''), i.inci_name) IS NOT NULL
  ),
  catalog_formulas AS (
    SELECT
      product_id,
      array_agg(normalized_token ORDER BY position) AS tokens
    FROM catalog_tokens
    GROUP BY product_id
  ),
  catalog_counts AS (
    SELECT product_id, normalized_token, count(*) AS token_count
    FROM catalog_tokens
    GROUP BY product_id, normalized_token
  ),
  token_overlaps AS (
    SELECT
      cc.product_id,
      sum(least(cc.token_count, ic.token_count)) AS matching_tokens
    FROM catalog_counts cc
    JOIN input_counts ic USING (normalized_token)
    GROUP BY cc.product_id
  ),
  scores AS (
    SELECT
      cf.product_id,
      (
        coalesce(o.matching_tokens, 0)::REAL
        / greatest(cardinality(cf.tokens), cardinality(inf.tokens))
      )::REAL AS similarity,
      cf.tokens = inf.tokens AS is_exact
    FROM catalog_formulas cf
    CROSS JOIN input_formula inf
    LEFT JOIN token_overlaps o ON o.product_id = cf.product_id
    WHERE cardinality(inf.tokens) > 0
  )
  SELECT scores.product_id, scores.similarity, scores.is_exact
  FROM scores
  WHERE scores.is_exact
     OR scores.similarity >= greatest(0.0, least(p_similarity_threshold, 1.0))
  ORDER BY scores.is_exact DESC, scores.similarity DESC, scores.product_id
  LIMIT 1;
$$;

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
  v_formula_tokens TEXT[];
  v_formula_lock TEXT;
  v_existing     UUID;
  v_brand_id     UUID;
  v_brand_norm   TEXT;
  v_brand_slug   TEXT;
  v_product_id   UUID := gen_random_uuid();
  v_product_slug TEXT;
  v_ingredient   UUID;
  v_product_ingredient UUID;
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
      AND resolution IN ('unresolved', 'pending_human')
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

  -- Compare the kept ingredient sequence directly with existing products.
  SELECT
    array_agg(raw_token ORDER BY position),
    string_agg(inci_normalize(raw_token), '|' ORDER BY position)
  INTO v_formula_tokens, v_formula_lock
  FROM submission_tokens
  WHERE submission_id = p_id AND resolution <> 'junk';

  -- The normalized formula is only a transient lock key. Nothing is stored.
  PERFORM pg_advisory_xact_lock(hashtext(v_formula_lock));

  SELECT match.product_id INTO v_existing
  FROM find_product_formula_match(v_formula_tokens, 1.0) AS match
  WHERE match.is_exact
  LIMIT 1;
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
    VALUES (v_product_id, v_position, t.matched_ingredient_id)
    RETURNING id INTO v_product_ingredient;

    INSERT INTO product_ingredient_metadata
      (product_ingredient_id, raw_inci_token, is_matched)
    VALUES (
      v_product_ingredient,
      t.raw_token,
      t.matched_ingredient_id IS NOT NULL
    );
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

-- Remove both historical storage locations. The submission list and the
-- catalog ingredient rows are now the source of truth.
ALTER TABLE product_submissions
  DROP COLUMN IF EXISTS ingredient_fingerprint;
ALTER TABLE products
  DROP COLUMN IF EXISTS ingredient_fingerprint;
DROP TABLE IF EXISTS product_metadata;

REVOKE EXECUTE ON FUNCTION find_product_formula_match(TEXT[], REAL)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION find_product_formula_match(TEXT[], REAL)
  TO service_role;
