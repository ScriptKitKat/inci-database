ALTER TABLE public.ingredient_information
  ADD COLUMN IF NOT EXISTS cosing_information JSONB NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_constraint
    WHERE conrelid = 'public.ingredient_information'::regclass
      AND conname = 'ingredient_information_cosing_information_check'
  ) THEN
    ALTER TABLE public.ingredient_information
      ADD CONSTRAINT ingredient_information_cosing_information_check
      CHECK (jsonb_typeof(cosing_information) = 'object');
  END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS ingredient_information_cosing_gin
  ON public.ingredient_information USING GIN (cosing_information);
CREATE INDEX IF NOT EXISTS ingredient_information_cas_idx
  ON public.ingredient_information ((cosing_information ->> 'cas_number'))
  WHERE cosing_information ? 'cas_number';

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
  v_existing     UUID;
  v_same_identity UUID;
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

  v_brand_norm := upper(trim(s.brand_name));
  PERFORM pg_advisory_xact_lock(hashtext(
    'product:' || v_brand_norm || '|'
    || regexp_replace(inci_normalize(trim(s.product_name)), '[[:space:]]+', ' ', 'g')
  ));

  SELECT array_agg(coalesce(st.matched_ingredient_id, i.id) ORDER BY st.position)
  INTO v_formula_ingredient_ids
  FROM submission_tokens st
  LEFT JOIN ingredients i
    ON st.resolution = 'new_ingredient'
   AND i.normalized_name = inci_normalize(st.canonical_name)
  WHERE st.submission_id = p_id AND st.resolution <> 'junk';

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

  SELECT identity.product_id INTO v_same_identity
  FROM find_product_by_identity(s.brand_name, s.product_name) AS identity;
  IF v_same_identity IS NOT NULL
      AND (s.verification -> 'existing_product' ->> 'product_id')
          IS DISTINCT FROM v_same_identity::TEXT THEN
    UPDATE product_submissions
    SET status = 'pending_human', locked_at = NULL,
        verification = verification || jsonb_build_object(
          'verdict', 'same_name_different_formula',
          'existing_product', jsonb_build_object('product_id', v_same_identity))
    WHERE id = p_id;
    INSERT INTO submission_audit (submission_id, action, actor, payload)
    VALUES (p_id, 'pending_human', v_actor,
            jsonb_build_object('trigger', 'same_name_different_formula',
                               'product_id', v_same_identity));
    RETURN 'pending_human';
  END IF;

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

REVOKE EXECUTE ON FUNCTION apply_product_submission(UUID, TEXT)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION apply_product_submission(UUID, TEXT) TO service_role;
