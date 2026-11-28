ALTER TABLE public.ingredient_enrichment_queue
  ADD COLUMN anthropic_batch_id TEXT,
  ADD COLUMN claim_id UUID,
  ADD COLUMN locked_at TIMESTAMPTZ,
  ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  ADD COLUMN review_reason TEXT CHECK (length(review_reason) <= 500),
  DROP CONSTRAINT ingredient_enrichment_queue_status_check,
  ADD CONSTRAINT ingredient_enrichment_queue_status_check CHECK (status IN (
    'unfilled', 'ingredient_information_filled', 'ingredient_description_filled', 'pending_human'
  ));

CREATE OR REPLACE FUNCTION public.ingredient_enrichment_context(p_ingredient_id UUID)
RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  RETURN (
    SELECT jsonb_build_object(
      'inci_name', i.inci_name,
      'aliases', COALESCE((SELECT jsonb_agg(a.alias ORDER BY a.alias)
        FROM ingredient_aliases a WHERE a.ingredient_id = i.id), '[]'::jsonb),
      'information', (SELECT to_jsonb(x) - 'id' - 'ingredient_id' - 'created_at' - 'updated_at'
        FROM ingredient_information x WHERE x.ingredient_id = i.id),
      'writeup', (SELECT to_jsonb(w) - 'id' - 'ingredient_id' - 'created_at' - 'updated_at'
        FROM ingredient_writeups w WHERE w.ingredient_id = i.id),
      'allowed_functions', COALESCE((SELECT jsonb_agg(f ORDER BY f) FROM (
        SELECT DISTINCT unnest(functions) AS f FROM ingredient_information
      ) vocabulary), '[]'::jsonb)
    ) FROM ingredients i WHERE i.id = p_ingredient_id
  );
END;
$$;

CREATE OR REPLACE FUNCTION public.fail_ingredient_enrichment(
  p_ingredient_id UUID, p_claim_id UUID, p_reason TEXT, p_max_attempts INTEGER DEFAULT 3
) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  UPDATE ingredient_enrichment_queue
  SET attempt_count = attempt_count + 1,
      status = CASE WHEN attempt_count + 1 >= greatest(p_max_attempts, 1)
        THEN 'pending_human' ELSE status END,
      review_reason = left(p_reason, 500), claim_id = NULL, locked_at = NULL,
      anthropic_batch_id = NULL
  WHERE ingredient_id = p_ingredient_id AND claim_id = p_claim_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.review_ingredient_enrichment(
  p_ingredient_id UUID, p_claim_id UUID, p_reason TEXT
) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  UPDATE ingredient_enrichment_queue
  SET status = 'pending_human', review_reason = left(p_reason, 500),
      claim_id = NULL, locked_at = NULL, anthropic_batch_id = NULL
  WHERE ingredient_id = p_ingredient_id AND claim_id = p_claim_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.claim_ingredient_enrichment(
  p_claim_id UUID, p_limit INTEGER DEFAULT 10, p_max_attempts INTEGER DEFAULT 3,
  p_stale_minutes INTEGER DEFAULT 30, p_batch_stale_minutes INTEGER DEFAULT 2880
) RETURNS SETOF ingredient_enrichment_queue
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  q ingredient_enrichment_queue%ROWTYPE;
BEGIN
  PERFORM assert_curator_or_service();
  IF p_claim_id IS NULL OR p_limit < 1 OR p_limit > 100 OR p_max_attempts < 1
     OR p_stale_minutes < 1 OR p_batch_stale_minutes < 1440 THEN
    RAISE EXCEPTION 'invalid enrichment claim settings';
  END IF;
  IF EXISTS (SELECT 1 FROM ingredient_enrichment_queue WHERE claim_id = p_claim_id) THEN
    RETURN QUERY SELECT * FROM ingredient_enrichment_queue WHERE claim_id = p_claim_id;
    RETURN;
  END IF;
  FOR q IN SELECT * FROM ingredient_enrichment_queue
    WHERE locked_at < now() - make_interval(mins => CASE WHEN anthropic_batch_id IS NULL
      THEN p_stale_minutes ELSE p_batch_stale_minutes END)
      AND claim_id IS NOT NULL
    FOR UPDATE SKIP LOCKED
  LOOP
    PERFORM fail_ingredient_enrichment(q.ingredient_id, q.claim_id,
      'stale_enrichment_claim', p_max_attempts);
  END LOOP;
  WITH exhausted AS (
    SELECT ingredient_id FROM ingredient_enrichment_queue
    WHERE status IN ('unfilled', 'ingredient_information_filled')
      AND attempt_count >= p_max_attempts AND claim_id IS NULL
    FOR UPDATE SKIP LOCKED
  )
  UPDATE ingredient_enrichment_queue target SET status = 'pending_human',
    review_reason = 'enrichment_attempts_exhausted'
  FROM exhausted WHERE target.ingredient_id = exhausted.ingredient_id;
  RETURN QUERY
  WITH candidates AS (
    SELECT ingredient_id FROM ingredient_enrichment_queue
    WHERE status IN ('unfilled', 'ingredient_information_filled')
      AND attempt_count < p_max_attempts AND claim_id IS NULL
    ORDER BY created_at, ingredient_id
    FOR UPDATE SKIP LOCKED LIMIT p_limit
  )
  UPDATE ingredient_enrichment_queue target
  SET claim_id = p_claim_id, locked_at = now(), review_reason = NULL
  FROM candidates WHERE target.ingredient_id = candidates.ingredient_id
  RETURNING target.*;
END;
$$;

CREATE OR REPLACE FUNCTION public.attach_ingredient_enrichment_batch(
  p_claim_id UUID, p_batch_id TEXT, p_count INTEGER
) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_count INTEGER;
BEGIN
  PERFORM assert_curator_or_service();
  IF nullif(trim(p_batch_id), '') IS NULL OR p_count < 1 THEN
    RAISE EXCEPTION 'invalid enrichment batch';
  END IF;
  PERFORM 1 FROM ingredient_enrichment_queue WHERE claim_id = p_claim_id FOR UPDATE;
  SELECT count(*) INTO v_count FROM ingredient_enrichment_queue
    WHERE claim_id = p_claim_id AND (anthropic_batch_id IS NULL OR anthropic_batch_id = p_batch_id);
  IF v_count <> p_count THEN RAISE EXCEPTION 'stale enrichment claim'; END IF;
  UPDATE ingredient_enrichment_queue SET anthropic_batch_id = p_batch_id, locked_at = now()
  WHERE claim_id = p_claim_id AND anthropic_batch_id IS NULL;
END;
$$;

CREATE OR REPLACE FUNCTION public.fetch_ingredient_enrichment_batches()
RETURNS SETOF ingredient_enrichment_queue
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  RETURN QUERY SELECT * FROM ingredient_enrichment_queue
    WHERE anthropic_batch_id IS NOT NULL AND claim_id IS NOT NULL;
END;
$$;

CREATE OR REPLACE FUNCTION public.apply_ingredient_enrichment(
  p_ingredient_id UUID, p_claim_id UUID, p_payload JSONB,
  p_threshold REAL DEFAULT 0.8, p_max_attempts INTEGER DEFAULT 3
) RETURNS TEXT
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  q ingredient_enrichment_queue%ROWTYPE;
  v_functions TEXT[];
  v_facts TEXT[];
  v_information BOOLEAN;
  v_description BOOLEAN;
  v_status TEXT;
BEGIN
  PERFORM assert_curator_or_service();
  SELECT * INTO q FROM ingredient_enrichment_queue WHERE ingredient_id = p_ingredient_id FOR UPDATE;
  IF q.ingredient_id IS NULL THEN RAISE EXCEPTION 'enrichment queue row missing'; END IF;
  IF q.claim_id IS NULL THEN RETURN q.status; END IF;
  IF q.claim_id IS DISTINCT FROM p_claim_id THEN RAISE EXCEPTION 'stale enrichment claim'; END IF;
  IF p_threshold IS NULL OR p_threshold < 0 OR p_threshold > 1 THEN
    RAISE EXCEPTION 'invalid enrichment threshold';
  END IF;
  IF jsonb_typeof(p_payload) IS DISTINCT FROM 'object'
    OR NOT p_payload ?& ARRAY['rating','functions','quick_facts','summary','details','confidence','rationale']
    OR p_payload - ARRAY['rating','functions','quick_facts','summary','details','confidence','rationale'] <> '{}'
    OR jsonb_typeof(p_payload->'confidence') IS DISTINCT FROM 'number'
    OR (p_payload->>'confidence')::numeric NOT BETWEEN 0 AND 1
    OR jsonb_typeof(p_payload->'rationale') IS DISTINCT FROM 'string'
    OR length(trim(p_payload->>'rationale')) NOT BETWEEN 1 AND 500
    OR (p_payload->'rating' <> 'null' AND (jsonb_typeof(p_payload->'rating') <> 'string'
      OR p_payload->>'rating' NOT IN ('ew_ew','okie','yippe','wowza')))
    OR (p_payload->'functions' <> 'null' AND jsonb_typeof(p_payload->'functions') <> 'array')
    OR (p_payload->'quick_facts' <> 'null' AND jsonb_typeof(p_payload->'quick_facts') <> 'array')
    OR (p_payload->'summary' <> 'null' AND (jsonb_typeof(p_payload->'summary') <> 'string'
      OR length(trim(p_payload->>'summary')) NOT BETWEEN 1 AND 2000))
    OR (p_payload->'details' <> 'null' AND (jsonb_typeof(p_payload->'details') <> 'string'
      OR length(trim(p_payload->>'details')) NOT BETWEEN 1 AND 10000)) THEN
    PERFORM review_ingredient_enrichment(p_ingredient_id, p_claim_id, 'invalid_enrichment_result');
    RETURN 'pending_human';
  END IF;
  IF (p_payload->>'confidence')::numeric < p_threshold THEN
    PERFORM review_ingredient_enrichment(p_ingredient_id, p_claim_id, 'enrichment_confidence_below_threshold');
    RETURN 'pending_human';
  END IF;
  SELECT coalesce(array_agg(value #>> '{}'), '{}') INTO v_functions
    FROM jsonb_array_elements(nullif(p_payload->'functions', 'null'));
  SELECT coalesce(array_agg(value #>> '{}'), '{}') INTO v_facts
    FROM jsonb_array_elements(nullif(p_payload->'quick_facts', 'null'));
  IF cardinality(v_functions) > 100 OR cardinality(v_facts) > 10
    OR EXISTS (SELECT 1 FROM jsonb_array_elements(
      coalesce(nullif(p_payload->'functions','null'), '[]') ||
      coalesce(nullif(p_payload->'quick_facts','null'), '[]')) x
      WHERE jsonb_typeof(x) <> 'string' OR length(trim(x #>> '{}')) NOT BETWEEN 1 AND 500)
    OR cardinality(v_functions) <> (SELECT count(DISTINCT x) FROM unnest(v_functions) x)
    OR cardinality(v_facts) <> (SELECT count(DISTINCT x) FROM unnest(v_facts) x)
    OR EXISTS (SELECT 1 FROM unnest(v_functions) f WHERE NOT EXISTS (
      SELECT 1 FROM ingredient_information i WHERE f = ANY(i.functions))) THEN
    PERFORM review_ingredient_enrichment(p_ingredient_id, p_claim_id, 'invalid_enrichment_result');
    RETURN 'pending_human';
  END IF;
  INSERT INTO ingredient_information (ingredient_id) VALUES (p_ingredient_id) ON CONFLICT DO NOTHING;
  INSERT INTO ingredient_writeups (ingredient_id, editorial_metadata)
    VALUES (p_ingredient_id, '{"status":"draft"}') ON CONFLICT DO NOTHING;
  UPDATE ingredient_information
  SET rating = coalesce(rating, (p_payload->>'rating')::ingredient_rating),
    functions = CASE WHEN cardinality(functions) = 0 THEN v_functions ELSE functions END
  WHERE ingredient_id = p_ingredient_id AND (
    (rating IS NULL AND p_payload->>'rating' IS NOT NULL)
    OR (cardinality(functions) = 0 AND cardinality(v_functions) > 0));
  UPDATE ingredient_writeups
  SET quick_facts = CASE WHEN cardinality(quick_facts) = 0 THEN v_facts ELSE quick_facts END,
    summary = CASE WHEN nullif(trim(summary), '') IS NULL THEN p_payload->>'summary' ELSE summary END,
    details = CASE WHEN nullif(trim(details), '') IS NULL THEN p_payload->>'details' ELSE details END,
    editorial_metadata = CASE WHEN nullif(editorial_metadata->>'status', '') IS NULL
      THEN editorial_metadata || '{"status":"draft"}'::jsonb ELSE editorial_metadata END
  WHERE ingredient_id = p_ingredient_id AND (
    (cardinality(quick_facts) = 0 AND cardinality(v_facts) > 0)
    OR (nullif(trim(summary), '') IS NULL AND p_payload->>'summary' IS NOT NULL)
    OR (nullif(trim(details), '') IS NULL AND p_payload->>'details' IS NOT NULL));
  SELECT rating IS NOT NULL AND cardinality(functions) > 0 INTO v_information
    FROM ingredient_information WHERE ingredient_id = p_ingredient_id;
  SELECT cardinality(quick_facts) > 0 AND nullif(trim(summary), '') IS NOT NULL
    AND nullif(trim(details), '') IS NOT NULL INTO v_description
    FROM ingredient_writeups WHERE ingredient_id = p_ingredient_id;
  v_status := CASE WHEN v_information THEN 'ingredient_information_filled' ELSE 'unfilled' END;
  UPDATE ingredient_enrichment_queue SET status = v_status WHERE ingredient_id = p_ingredient_id;
  IF v_information AND v_description THEN v_status := 'ingredient_description_filled'; END IF;
  UPDATE ingredient_enrichment_queue SET status = v_status, anthropic_batch_id = NULL,
    claim_id = NULL, locked_at = NULL, review_reason = NULL
  WHERE ingredient_id = p_ingredient_id;
  IF v_status <> 'ingredient_description_filled' THEN
    UPDATE ingredient_enrichment_queue SET claim_id = p_claim_id WHERE ingredient_id = p_ingredient_id;
    PERFORM fail_ingredient_enrichment(p_ingredient_id, p_claim_id, 'incomplete_enrichment', p_max_attempts);
  END IF;
  RETURN (SELECT status FROM ingredient_enrichment_queue WHERE ingredient_id = p_ingredient_id);
END;
$$;

REVOKE ALL ON FUNCTION public.ingredient_enrichment_context(UUID) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.fail_ingredient_enrichment(UUID, UUID, TEXT, INTEGER) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.review_ingredient_enrichment(UUID, UUID, TEXT) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.claim_ingredient_enrichment(UUID, INTEGER, INTEGER, INTEGER, INTEGER) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.attach_ingredient_enrichment_batch(UUID, TEXT, INTEGER) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.fetch_ingredient_enrichment_batches() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.apply_ingredient_enrichment(UUID, UUID, JSONB, REAL, INTEGER) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.ingredient_enrichment_context(UUID) TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION public.fail_ingredient_enrichment(UUID, UUID, TEXT, INTEGER) TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION public.review_ingredient_enrichment(UUID, UUID, TEXT) TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION public.claim_ingredient_enrichment(UUID, INTEGER, INTEGER, INTEGER, INTEGER) TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION public.attach_ingredient_enrichment_batch(UUID, TEXT, INTEGER) TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION public.fetch_ingredient_enrichment_batches() TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION public.apply_ingredient_enrichment(UUID, UUID, JSONB, REAL, INTEGER) TO service_role, authenticated;
