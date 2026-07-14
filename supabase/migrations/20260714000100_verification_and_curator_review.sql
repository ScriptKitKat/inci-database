-- Durable verification batches and the private curator-review surface.

ALTER TABLE product_submissions DROP CONSTRAINT product_submissions_status_check;
ALTER TABLE product_submissions
  ADD CONSTRAINT product_submissions_status_check CHECK (status IN (
    'received', 'triaging', 'verifying', 'batch_preparing', 'decision_ready',
    'pending_human', 'approved', 'rejected', 'duplicate', 'failed'
  )),
  ADD COLUMN verification_group_id UUID;

CREATE TABLE submission_verification_batches (
  id                 UUID PRIMARY KEY,
  anthropic_batch_id TEXT UNIQUE,
  submission_ids     UUID[] NOT NULL,
  request_count      INTEGER NOT NULL CHECK (request_count > 0),
  payload_bytes      INTEGER NOT NULL CHECK (payload_bytes > 0),
  status             TEXT NOT NULL CHECK (
    status IN ('preparing', 'submitted', 'ended', 'failed', 'orphaned')
  ),
  last_error         TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_submission_verification_batches_updated
  BEFORE UPDATE ON submission_verification_batches
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE submission_verification_batches ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION claim_submission_verification(p_limit INTEGER)
RETURNS SETOF product_submissions
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_group UUID := gen_random_uuid();
BEGIN
  PERFORM assert_curator_or_service();
  RETURN QUERY
  WITH claimed AS (
    SELECT s.id
    FROM product_submissions s
    WHERE s.status = 'verifying' AND s.anthropic_batch_id IS NULL
    ORDER BY s.created_at, s.id
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED
  )
  UPDATE product_submissions s
  SET status = 'batch_preparing', locked_at = now(), verification_group_id = v_group
  FROM claimed
  WHERE s.id = claimed.id
  RETURNING s.*;
END;
$$;

CREATE OR REPLACE FUNCTION attach_submission_verification_batch(
  p_group_id UUID,
  p_anthropic_batch_id TEXT
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_ids UUID[];
BEGIN
  PERFORM assert_curator_or_service();
  SELECT submission_ids INTO v_ids
  FROM submission_verification_batches
  WHERE id = p_group_id AND status = 'preparing'
  FOR UPDATE;
  IF v_ids IS NULL THEN
    RAISE EXCEPTION 'verification group % is not preparing', p_group_id;
  END IF;

  UPDATE product_submissions
  SET status = 'verifying', anthropic_batch_id = p_anthropic_batch_id,
      verification_group_id = p_group_id, locked_at = NULL
  WHERE id = ANY(v_ids) AND status = 'batch_preparing';
  IF NOT FOUND OR (SELECT count(*) FROM product_submissions WHERE id = ANY(v_ids)
      AND anthropic_batch_id = p_anthropic_batch_id) <> cardinality(v_ids) THEN
    RAISE EXCEPTION 'could not atomically attach verification group %', p_group_id;
  END IF;

  UPDATE submission_verification_batches
  SET anthropic_batch_id = p_anthropic_batch_id, status = 'submitted'
  WHERE id = p_group_id;
END;
$$;

CREATE OR REPLACE FUNCTION create_submission_verification_batch(
  p_group_id UUID,
  p_submission_ids UUID[],
  p_request_count INTEGER,
  p_payload_bytes INTEGER
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_updated INTEGER;
BEGIN
  PERFORM assert_curator_or_service();
  INSERT INTO submission_verification_batches
    (id, submission_ids, request_count, payload_bytes, status)
  VALUES
    (p_group_id, p_submission_ids, p_request_count, p_payload_bytes, 'preparing');
  UPDATE product_submissions
  SET verification_group_id = p_group_id
  WHERE id = ANY(p_submission_ids) AND status = 'batch_preparing';
  GET DIAGNOSTICS v_updated = ROW_COUNT;
  IF v_updated <> cardinality(p_submission_ids) THEN
    RAISE EXCEPTION 'could not prepare every submission in group %', p_group_id;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION release_submission_verification_batch(
  p_group_id UUID,
  p_error TEXT,
  p_max_attempts INTEGER DEFAULT 3,
  p_orphaned BOOLEAN DEFAULT false
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_ids UUID[];
BEGIN
  PERFORM assert_curator_or_service();
  SELECT submission_ids INTO v_ids
  FROM submission_verification_batches WHERE id = p_group_id FOR UPDATE;
  IF v_ids IS NULL THEN
    RAISE EXCEPTION 'verification group % not found', p_group_id;
  END IF;

  UPDATE submission_verification_batches
  SET status = CASE WHEN p_orphaned THEN 'orphaned' ELSE 'failed' END,
      last_error = left(p_error, 2000)
  WHERE id = p_group_id;

  UPDATE product_submissions
  SET status = CASE WHEN attempt_count >= p_max_attempts THEN 'failed' ELSE 'received' END,
      anthropic_batch_id = NULL, verification_group_id = NULL, locked_at = NULL,
      last_error = left(p_error, 2000)
  WHERE id = ANY(v_ids)
    AND (verification_group_id = p_group_id OR anthropic_batch_id = (
      SELECT anthropic_batch_id FROM submission_verification_batches WHERE id = p_group_id
    ));

  INSERT INTO submission_audit (submission_id, action, actor, payload)
  SELECT id, CASE WHEN p_orphaned THEN 'verification_batch_orphaned'
                  ELSE 'verification_batch_failed' END,
         'worker', jsonb_build_object('group_id', p_group_id, 'error', left(p_error, 2000))
  FROM product_submissions WHERE id = ANY(v_ids);
END;
$$;

CREATE OR REPLACE FUNCTION recover_stale_submission_verification(
  p_older_than_minutes INTEGER,
  p_max_attempts INTEGER DEFAULT 3
)
RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  row RECORD;
  v_count INTEGER := 0;
  v_untracked INTEGER := 0;
BEGIN
  PERFORM assert_curator_or_service();
  FOR row IN
    SELECT id FROM submission_verification_batches
    WHERE status = 'preparing'
      AND created_at < now() - make_interval(mins => p_older_than_minutes)
    FOR UPDATE SKIP LOCKED
  LOOP
    PERFORM release_submission_verification_batch(
      row.id, 'stale preparing verification group', p_max_attempts, true
    );
    v_count := v_count + 1;
  END LOOP;
  WITH released AS (
    UPDATE product_submissions s
    SET status = CASE WHEN attempt_count >= p_max_attempts THEN 'failed' ELSE 'received' END,
        verification_group_id = NULL, locked_at = NULL,
        last_error = 'stale untracked verification claim'
    WHERE status = 'batch_preparing'
      AND locked_at < now() - make_interval(mins => p_older_than_minutes)
      AND NOT EXISTS (
        SELECT 1 FROM submission_verification_batches b
        WHERE b.id = s.verification_group_id
      )
    RETURNING id
  ), audited AS (
    INSERT INTO submission_audit (submission_id, action, actor, payload)
    SELECT id, 'verification_claim_released', 'worker',
      '{"error":"stale untracked verification claim"}'::jsonb
    FROM released
    RETURNING 1
  )
  SELECT count(*) INTO v_untracked FROM audited;
  RETURN v_count + v_untracked;
END;
$$;

CREATE TABLE brand_product_domains (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  normalized_brand_name TEXT NOT NULL,
  domain                TEXT NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (normalized_brand_name, domain)
);
ALTER TABLE brand_product_domains ENABLE ROW LEVEL SECURITY;

CREATE TABLE curator_reviewers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name    TEXT NOT NULL,
  normalized_name TEXT NOT NULL UNIQUE,
  active          BOOLEAN NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE curator_reviewers ENABLE ROW LEVEL SECURITY;
INSERT INTO curator_reviewers (display_name, normalized_name)
VALUES ('Priscilla', 'priscilla') ON CONFLICT (normalized_name) DO NOTHING;

DROP FUNCTION resolve_submission_token(UUID, TEXT, UUID, TEXT);
CREATE OR REPLACE FUNCTION resolve_submission_token(
  p_token_id       UUID,
  p_resolution     TEXT,
  p_ingredient_id  UUID DEFAULT NULL,
  p_canonical_name TEXT DEFAULT NULL,
  p_actor          TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  t submission_tokens%ROWTYPE;
BEGIN
  PERFORM assert_curator_or_service();
  IF p_resolution NOT IN ('matched', 'new_ingredient', 'junk') THEN
    RAISE EXCEPTION 'invalid resolution %', p_resolution;
  END IF;
  SELECT * INTO t FROM submission_tokens WHERE id = p_token_id FOR UPDATE;
  IF t.id IS NULL THEN RAISE EXCEPTION 'token % not found', p_token_id; END IF;
  IF NOT EXISTS (SELECT 1 FROM product_submissions
      WHERE id = t.submission_id AND status = 'pending_human') THEN
    RAISE EXCEPTION 'token % is not awaiting human review', p_token_id;
  END IF;
  IF p_resolution = 'matched' AND (p_ingredient_id IS NULL OR NOT EXISTS (
      SELECT 1 FROM ingredients WHERE id = p_ingredient_id)) THEN
    RAISE EXCEPTION 'matched resolution requires an existing ingredient id';
  END IF;
  IF p_resolution = 'new_ingredient'
      AND nullif(trim(p_canonical_name), '') IS NULL THEN
    RAISE EXCEPTION 'new_ingredient resolution requires a canonical name';
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
  VALUES (t.submission_id, 'resolve_token', coalesce(p_actor, 'service'),
    jsonb_build_object('token_id', p_token_id, 'raw_token', t.raw_token,
      'resolution', p_resolution, 'ingredient_id', p_ingredient_id,
      'canonical_name', p_canonical_name));
END;
$$;

REVOKE ALL ON submission_verification_batches, brand_product_domains,
  curator_reviewers FROM PUBLIC, anon, authenticated;
GRANT ALL ON submission_verification_batches, brand_product_domains,
  curator_reviewers TO service_role;
REVOKE EXECUTE ON FUNCTION claim_submission_verification(INTEGER),
  create_submission_verification_batch(UUID, UUID[], INTEGER, INTEGER),
  attach_submission_verification_batch(UUID, TEXT),
  release_submission_verification_batch(UUID, TEXT, INTEGER, BOOLEAN),
  recover_stale_submission_verification(INTEGER, INTEGER),
  resolve_submission_token(UUID, TEXT, UUID, TEXT, TEXT)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION claim_submission_verification(INTEGER),
  create_submission_verification_batch(UUID, UUID[], INTEGER, INTEGER),
  attach_submission_verification_batch(UUID, TEXT),
  release_submission_verification_batch(UUID, TEXT, INTEGER, BOOLEAN),
  recover_stale_submission_verification(INTEGER, INTEGER),
  resolve_submission_token(UUID, TEXT, UUID, TEXT, TEXT)
  TO service_role;
