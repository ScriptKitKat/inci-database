-- User-submitted product verification pipeline.
--
-- Review-first staging: submissions and their parsed ingredient tokens are
-- verified (deterministic evidence -> LLM batch -> human) BEFORE anything
-- touches the canonical catalog. apply_product_submission() is the only
-- writer to brands/products/product_ingredients/ingredients, and a canonical
-- ingredient spelling can only come from an authoritative source string
-- (token.canonical_name), never from LLM output. See
-- docs/superpowers/specs/2026-07-09-user-submission-pipeline-design.md.

ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'user_submission';

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

-- The linked project removed these normalized metadata tables outside the
-- recorded migration history. Recreate them here so this migration is safe on
-- both a clean replay (where 20260709000100 already created them) and the live
-- schema. Existing rows are preserved by IF NOT EXISTS.
CREATE TABLE IF NOT EXISTS product_ingredient_metadata (
  product_ingredient_id UUID PRIMARY KEY
    REFERENCES product_ingredients(id) ON DELETE CASCADE,
  raw_inci_token        TEXT NOT NULL,
  is_matched            BOOLEAN NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS product_ingredient_metadata_matched_idx
  ON product_ingredient_metadata (is_matched);

ALTER TABLE product_ingredient_metadata ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS public_read_product_ingredient_metadata
  ON product_ingredient_metadata;
CREATE POLICY public_read_product_ingredient_metadata
  ON product_ingredient_metadata FOR SELECT USING (true);

CREATE TABLE IF NOT EXISTS product_metadata (
  product_id             UUID PRIMARY KEY
    REFERENCES products(id) ON DELETE CASCADE,
  ingredient_fingerprint TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE product_metadata ENABLE ROW LEVEL SECURITY;

CREATE TABLE product_submissions (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submitted_by           UUID REFERENCES auth.users(id),
  brand_name             TEXT NOT NULL,
  product_name           TEXT NOT NULL,
  raw_ingredient_text    TEXT NOT NULL,
  ingredient_fingerprint TEXT,
  status TEXT NOT NULL DEFAULT 'received' CHECK (status IN (
    'received',       -- awaiting intake
    'triaging',       -- claimed by intake worker (transient, locked)
    'verifying',      -- awaiting/inside LLM batch (batch_id NULL = not yet submitted)
    'decision_ready', -- fully auto-resolved; awaiting apply
    'pending_human',  -- needs curator review
    'approved',
    'rejected',
    'duplicate',
    'failed'
  )),
  -- {found, source_name, source_url, overlap, verdict, online_tokens?}
  -- online_tokens is stored only when verdict = 'divergent' (review diff).
  verification           JSONB NOT NULL DEFAULT '{}'::jsonb,
  anthropic_batch_id     TEXT,
  product_id             UUID REFERENCES products(id),
  locked_at              TIMESTAMPTZ,
  attempt_count          INTEGER NOT NULL DEFAULT 0,
  last_error             TEXT,
  reviewed_by            UUID,
  reviewed_at            TIMESTAMPTZ,
  reject_reason          TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at           TIMESTAMPTZ
);

CREATE INDEX product_submissions_status_idx
  ON product_submissions (status, created_at);
CREATE INDEX product_submissions_fingerprint_idx
  ON product_submissions (ingredient_fingerprint)
  WHERE ingredient_fingerprint IS NOT NULL;
CREATE INDEX product_submissions_submitted_by_idx
  ON product_submissions (submitted_by)
  WHERE submitted_by IS NOT NULL;

CREATE TRIGGER trg_product_submissions_updated
  BEFORE UPDATE ON product_submissions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE submission_tokens (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id         UUID NOT NULL REFERENCES product_submissions(id) ON DELETE CASCADE,
  position              INTEGER NOT NULL,
  raw_token             TEXT NOT NULL,
  normalized_token      TEXT NOT NULL,
  matched_ingredient_id UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  match_type            TEXT,
  match_confidence      REAL,
  resolution TEXT NOT NULL DEFAULT 'unresolved' CHECK (resolution IN (
    'unresolved',     -- awaiting evidence/LLM
    'matched',        -- resolves to matched_ingredient_id
    'new_ingredient', -- created at apply; canonical_name from authoritative source
    'junk',           -- label noise; dropped at apply
    'unmatched_keep', -- human-only: keep as unmatched product_ingredients row
    'pending_human'
  )),
  -- Exact authoritative-source spelling (with the approved CosIng casing
  -- transform), or trusted curator input. The LLM never authors this value.
  canonical_name        TEXT,
  -- Compact: [{source, found, canonical, url, confidence}] - no raw payloads.
  evidence              JSONB NOT NULL DEFAULT '[]'::jsonb,
  resolution_source     TEXT CHECK (resolution_source IN
    ('exact_match', 'deterministic', 'llm', 'human')),
  UNIQUE (submission_id, position)
);

CREATE INDEX submission_tokens_submission_idx
  ON submission_tokens (submission_id);

CREATE TABLE curators (
  user_id    UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE submission_audit (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id UUID NOT NULL REFERENCES product_submissions(id) ON DELETE CASCADE,
  action        TEXT NOT NULL,
  actor         TEXT NOT NULL,
  payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX submission_audit_submission_idx
  ON submission_audit (submission_id, created_at);

-- New ingredients are usable immediately, but stay queued until both the
-- structured-information and editorial backfills have completed.
CREATE TABLE ingredient_enrichment_queue (
  ingredient_id UUID PRIMARY KEY REFERENCES ingredients(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'unfilled' CHECK (status IN (
    'unfilled',
    'ingredient_information_filled',
    'ingredient_description_filled'
  )),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ingredient_enrichment_queue_status_idx
  ON ingredient_enrichment_queue (status, created_at);

-- Fingerprints moved out of products in 20260709000100. Preserve the old
-- uniqueness guarantee on their normalized home.
CREATE UNIQUE INDEX IF NOT EXISTS product_metadata_fingerprint_unique_idx
  ON product_metadata (ingredient_fingerprint)
  WHERE ingredient_fingerprint IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Authorization helper
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_curator()
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (SELECT 1 FROM curators WHERE user_id = auth.uid());
$$;

-- Callers of curator-gated RPCs: service role (auth.uid() IS NULL, EXECUTE
-- granted below) or an authenticated curator.
CREATE OR REPLACE FUNCTION assert_curator_or_service()
RETURNS VOID
LANGUAGE plpgsql STABLE
AS $$
BEGIN
  IF auth.uid() IS NOT NULL AND NOT is_curator() THEN
    RAISE EXCEPTION 'not authorized: curator role required';
  END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- Worker RPCs (claim / fail)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION claim_product_submissions(
  p_from_status TEXT,
  p_to_status   TEXT,
  p_limit       INTEGER
)
RETURNS SETOF product_submissions
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  RETURN QUERY
  WITH claimed AS (
    SELECT s.id
    FROM product_submissions s
    WHERE s.status = p_from_status
    ORDER BY s.created_at, s.id
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED
  )
  UPDATE product_submissions s
  SET status = p_to_status,
      locked_at = now(),
      attempt_count = attempt_count + 1,
      last_error = NULL
  FROM claimed
  WHERE s.id = claimed.id
  RETURNING s.*;
END;
$$;

CREATE OR REPLACE FUNCTION fail_product_submission(
  p_id           UUID,
  p_error        TEXT,
  p_max_attempts INTEGER DEFAULT 3
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  UPDATE product_submissions
  SET status = CASE WHEN attempt_count >= p_max_attempts
                    THEN 'failed' ELSE 'received' END,
      locked_at = NULL,
      last_error = left(p_error, 2000)
  WHERE id = p_id;
END;
$$;

-- ---------------------------------------------------------------------------
-- Review RPCs
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION resolve_submission_token(
  p_token_id       UUID,
  p_resolution     TEXT,
  p_ingredient_id  UUID DEFAULT NULL,
  p_canonical_name TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  t submission_tokens%ROWTYPE;
BEGIN
  PERFORM assert_curator_or_service();

  IF p_resolution NOT IN ('matched', 'new_ingredient', 'junk', 'unmatched_keep') THEN
    RAISE EXCEPTION 'invalid resolution %', p_resolution;
  END IF;

  SELECT * INTO t FROM submission_tokens WHERE id = p_token_id FOR UPDATE;
  IF t.id IS NULL THEN
    RAISE EXCEPTION 'token % not found', p_token_id;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM product_submissions
    WHERE id = t.submission_id AND status = 'pending_human'
  ) THEN
    RAISE EXCEPTION 'token % is not awaiting human review', p_token_id;
  END IF;

  IF p_resolution = 'matched' THEN
    IF p_ingredient_id IS NULL
       OR NOT EXISTS (SELECT 1 FROM ingredients WHERE id = p_ingredient_id) THEN
      RAISE EXCEPTION 'matched resolution requires an existing ingredient id';
    END IF;
  ELSIF p_resolution = 'new_ingredient' THEN
    IF p_canonical_name IS NULL OR trim(p_canonical_name) = '' THEN
      RAISE EXCEPTION 'new_ingredient resolution requires a canonical name';
    END IF;
  END IF;

  UPDATE submission_tokens
  SET resolution = p_resolution,
      matched_ingredient_id = CASE WHEN p_resolution = 'matched'
                                   THEN p_ingredient_id ELSE NULL END,
      canonical_name = CASE WHEN p_resolution = 'new_ingredient'
                            THEN trim(p_canonical_name) ELSE NULL END,
      match_type = CASE WHEN p_resolution = 'matched' THEN match_type ELSE NULL END,
      match_confidence = CASE WHEN p_resolution = 'matched' THEN match_confidence ELSE NULL END,
      resolution_source = 'human'
  WHERE id = p_token_id;

  INSERT INTO submission_audit (submission_id, action, actor, payload)
  VALUES (
    t.submission_id,
    'resolve_token',
    coalesce(auth.uid()::text, 'service'),
    jsonb_build_object(
      'token_id', p_token_id,
      'raw_token', t.raw_token,
      'resolution', p_resolution,
      'ingredient_id', p_ingredient_id,
      'canonical_name', p_canonical_name
    )
  );
END;
$$;

CREATE OR REPLACE FUNCTION reject_product_submission(
  p_id     UUID,
  p_reason TEXT,
  p_actor  TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  UPDATE product_submissions
  SET status = 'rejected',
      reject_reason = p_reason,
      reviewed_by = auth.uid(),
      reviewed_at = now(),
      processed_at = now(),
      locked_at = NULL
  WHERE id = p_id
    AND status NOT IN ('approved', 'rejected');
  IF NOT FOUND THEN
    RAISE EXCEPTION 'submission % not found or already finalized', p_id;
  END IF;

  INSERT INTO submission_audit (submission_id, action, actor, payload)
  VALUES (p_id, 'reject', coalesce(p_actor, auth.uid()::text, 'service'),
          jsonb_build_object('reason', p_reason));
END;
$$;

-- ---------------------------------------------------------------------------
-- Apply: the only writer to canonical tables
-- ---------------------------------------------------------------------------

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
  v_fingerprint  TEXT;
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

  -- Fingerprint over kept tokens; race-safe duplicate check.
  SELECT md5(string_agg(upper(trim(raw_token)), '|' ORDER BY position))
  INTO v_fingerprint
  FROM submission_tokens
  WHERE submission_id = p_id AND resolution <> 'junk';

  -- Serialize identical fingerprints so concurrent submissions cannot both
  -- pass the duplicate check before either writes product_metadata.
  PERFORM pg_advisory_xact_lock(hashtext(v_fingerprint));

  SELECT m.product_id INTO v_existing
  FROM product_metadata m
  WHERE m.ingredient_fingerprint = v_fingerprint;
  IF v_existing IS NOT NULL THEN
    UPDATE product_submissions
    SET status = 'duplicate', product_id = v_existing,
        ingredient_fingerprint = v_fingerprint,
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

  INSERT INTO product_metadata (product_id, ingredient_fingerprint)
  VALUES (v_product_id, v_fingerprint);

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
      ingredient_fingerprint = v_fingerprint,
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

-- ---------------------------------------------------------------------------
-- Retention
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION purge_stale_submissions(p_days INTEGER DEFAULT 30)
RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_count INTEGER;
BEGIN
  PERFORM assert_curator_or_service();
  DELETE FROM product_submissions
  WHERE status IN ('rejected', 'duplicate')
    AND coalesce(processed_at, updated_at) < now() - make_interval(days => p_days);
  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END;
$$;

-- ---------------------------------------------------------------------------
-- RLS and grants
-- ---------------------------------------------------------------------------

ALTER TABLE product_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE submission_tokens   ENABLE ROW LEVEL SECURITY;
ALTER TABLE curators            ENABLE ROW LEVEL SECURITY;
ALTER TABLE submission_audit    ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_enrichment_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY submissions_insert_own ON product_submissions
  FOR INSERT TO authenticated
  WITH CHECK (submitted_by = auth.uid());

CREATE POLICY submissions_read_own_or_curator ON product_submissions
  FOR SELECT TO authenticated
  USING (submitted_by = auth.uid() OR is_curator());

CREATE POLICY tokens_read_own_or_curator ON submission_tokens
  FOR SELECT TO authenticated
  USING (
    is_curator() OR EXISTS (
      SELECT 1 FROM product_submissions s
      WHERE s.id = submission_tokens.submission_id
        AND s.submitted_by = auth.uid()
    )
  );

CREATE POLICY curators_read_self ON curators
  FOR SELECT TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY audit_read_curator ON submission_audit
  FOR SELECT TO authenticated
  USING (is_curator());

CREATE POLICY enrichment_queue_public_read ON ingredient_enrichment_queue
  FOR SELECT USING (true);

GRANT SELECT ON ingredient_enrichment_queue TO anon, authenticated;

-- Mutating access is RPC-only: no UPDATE/DELETE policies, and the RPCs are
-- SECURITY DEFINER with an internal curator/service check. Lock down EXECUTE.
REVOKE EXECUTE ON FUNCTION claim_product_submissions(TEXT, TEXT, INTEGER) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION fail_product_submission(UUID, TEXT, INTEGER) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION resolve_submission_token(UUID, TEXT, UUID, TEXT) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION reject_product_submission(UUID, TEXT, TEXT) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION apply_product_submission(UUID, TEXT) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION purge_stale_submissions(INTEGER) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION assert_curator_or_service() FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION is_curator() TO authenticated;
GRANT EXECUTE ON FUNCTION assert_curator_or_service() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION claim_product_submissions(TEXT, TEXT, INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION fail_product_submission(UUID, TEXT, INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION resolve_submission_token(UUID, TEXT, UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION reject_product_submission(UUID, TEXT, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION apply_product_submission(UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION purge_stale_submissions(INTEGER) TO authenticated, service_role;
