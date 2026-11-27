CREATE OR REPLACE FUNCTION public.submit_product_submission(
  p_brand_name          TEXT,
  p_product_name        TEXT,
  p_raw_ingredient_text TEXT
)
RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user    UUID := auth.uid();
  v_brand   TEXT := trim(coalesce(p_brand_name, ''));
  v_product TEXT := trim(coalesce(p_product_name, ''));
  v_label   TEXT := trim(coalesce(p_raw_ingredient_text, ''));
  v_id      UUID;
BEGIN
  IF v_user IS NULL THEN
    RAISE EXCEPTION 'not authorized: sign in to submit a product'
      USING ERRCODE = '42501';
  END IF;
  IF v_brand = '' OR length(v_brand) > 200 THEN
    RAISE EXCEPTION 'brand name must be 1-200 characters' USING ERRCODE = '22023';
  END IF;
  IF v_product = '' OR length(v_product) > 300 THEN
    RAISE EXCEPTION 'product name must be 1-300 characters' USING ERRCODE = '22023';
  END IF;
  IF v_label = '' OR length(v_label) > 20000 THEN
    RAISE EXCEPTION 'ingredient list must be 1-20000 characters' USING ERRCODE = '22023';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtext('submission:' || v_user::TEXT));

  SELECT id INTO v_id
  FROM product_submissions
  WHERE submitted_by = v_user
    AND upper(brand_name) = upper(v_brand)
    AND upper(product_name) = upper(v_product)
    AND raw_ingredient_text = v_label
    AND status IN ('received', 'triaging', 'verifying', 'batch_preparing',
                   'decision_ready', 'pending_human')
  ORDER BY created_at
  LIMIT 1;
  IF v_id IS NOT NULL THEN
    RETURN v_id;
  END IF;

  INSERT INTO product_submissions
    (submitted_by, brand_name, product_name, raw_ingredient_text)
  VALUES (v_user, v_brand, v_product, v_label)
  RETURNING id INTO v_id;

  INSERT INTO submission_audit (submission_id, action, actor, payload)
  VALUES (v_id, 'submitted', v_user::TEXT, '{}'::jsonb);

  RETURN v_id;
END;
$$;

REVOKE ALL ON FUNCTION public.submit_product_submission(TEXT, TEXT, TEXT)
  FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.submit_product_submission(TEXT, TEXT, TEXT)
  TO authenticated;

DROP POLICY IF EXISTS submissions_insert_own ON public.product_submissions;

REVOKE ALL ON public.product_submissions, public.submission_tokens,
  public.submission_audit FROM anon, authenticated;
GRANT SELECT (id, brand_name, product_name, status, product_id, reject_reason,
  created_at, updated_at, processed_at)
  ON public.product_submissions TO authenticated;
