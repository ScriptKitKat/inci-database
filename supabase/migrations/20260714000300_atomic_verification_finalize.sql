-- Apply one submission's verification results atomically. A stale batch may
-- finish after retry; the expected id prevents it from overwriting newer work.
CREATE OR REPLACE FUNCTION finalize_submission_verification(
  p_id UUID,
  p_expected_batch_id TEXT,
  p_token_updates JSONB,
  p_verification JSONB,
  p_status TEXT,
  p_trigger TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  s product_submissions%ROWTYPE;
  item JSONB;
  fields JSONB;
BEGIN
  PERFORM assert_curator_or_service();
  IF p_status NOT IN ('decision_ready', 'pending_human') THEN
    RAISE EXCEPTION 'invalid verification final status %', p_status;
  END IF;
  SELECT * INTO s FROM product_submissions WHERE id = p_id FOR UPDATE;
  IF s.id IS NULL THEN RAISE EXCEPTION 'submission % not found', p_id; END IF;
  IF p_expected_batch_id IS NOT NULL
      AND s.anthropic_batch_id IS DISTINCT FROM p_expected_batch_id THEN
    RETURN false;
  END IF;

  FOR item IN SELECT value FROM jsonb_array_elements(coalesce(p_token_updates, '[]'))
  LOOP
    fields := item -> 'fields';
    UPDATE submission_tokens
    SET resolution = fields ->> 'resolution',
        resolution_source = CASE WHEN fields ? 'resolution_source'
          THEN nullif(fields ->> 'resolution_source', '') ELSE resolution_source END,
        matched_ingredient_id = CASE WHEN fields ? 'matched_ingredient_id'
          THEN nullif(fields ->> 'matched_ingredient_id', '')::UUID
          ELSE matched_ingredient_id END,
        canonical_name = CASE WHEN fields ? 'canonical_name'
          THEN nullif(fields ->> 'canonical_name', '') ELSE canonical_name END,
        match_type = CASE WHEN fields ? 'match_type'
          THEN nullif(fields ->> 'match_type', '') ELSE match_type END,
        match_confidence = CASE WHEN fields ? 'match_confidence'
          THEN nullif(fields ->> 'match_confidence', '')::REAL ELSE match_confidence END
    WHERE id = (item ->> 'token_id')::UUID AND submission_id = p_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'verification token not found'; END IF;
    IF nullif(item ->> 'trigger', '') IS NOT NULL THEN
      INSERT INTO submission_audit (submission_id, action, actor, payload)
      VALUES (p_id, 'token_escalated', 'worker',
        jsonb_build_object('token_id', item ->> 'token_id',
                           'trigger', item ->> 'trigger'));
    END IF;
  END LOOP;

  UPDATE product_submissions
  SET status = p_status, verification = p_verification,
      anthropic_batch_id = NULL, verification_group_id = NULL, locked_at = NULL
  WHERE id = p_id;
  INSERT INTO submission_audit (submission_id, action, actor, payload)
  VALUES (p_id, 'verified', 'worker',
    jsonb_build_object(
      'verdict', p_verification ->> 'verdict', 'status', p_status,
      'submitted_coverage', p_verification -> 'submitted_coverage',
      'online_coverage', p_verification -> 'online_coverage'
    ) || CASE WHEN p_trigger IS NULL THEN '{}'::jsonb
              ELSE jsonb_build_object('trigger', p_trigger) END);
  RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION reject_product_submission(
  p_id UUID,
  p_reason TEXT,
  p_actor TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  PERFORM assert_curator_or_service();
  IF length(trim(coalesce(p_reason, ''))) < 10 THEN
    RAISE EXCEPTION 'rejection reason must be at least 10 characters';
  END IF;
  UPDATE product_submissions
  SET status = 'rejected', reject_reason = trim(p_reason), reviewed_by = auth.uid(),
      reviewed_at = now(), processed_at = now(), locked_at = NULL
  WHERE id = p_id AND status IN ('pending_human', 'decision_ready');
  IF NOT FOUND THEN
    RAISE EXCEPTION 'submission % is not reject-eligible', p_id;
  END IF;
  INSERT INTO submission_audit (submission_id, action, actor, payload)
  VALUES (p_id, 'reject', coalesce(p_actor, auth.uid()::text, 'service'),
          jsonb_build_object('reason', trim(p_reason)));
END;
$$;

REVOKE EXECUTE ON FUNCTION finalize_submission_verification(
  UUID, TEXT, JSONB, JSONB, TEXT, TEXT
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION finalize_submission_verification(
  UUID, TEXT, JSONB, JSONB, TEXT, TEXT
) TO service_role;
