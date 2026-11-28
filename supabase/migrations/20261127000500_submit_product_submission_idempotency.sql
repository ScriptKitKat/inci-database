-- Same authenticated user, same normalized draft, same open submission id.

CREATE OR REPLACE FUNCTION public.product_submission_fingerprint(
  p_brand_name          TEXT,
  p_product_name        TEXT,
  p_raw_ingredient_text TEXT
)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
SET search_path = public
AS $$
  SELECT md5(
    lower(btrim(regexp_replace(coalesce(p_brand_name, ''), '[[:space:]]+', ' ', 'g')))
    || chr(31)
    || lower(btrim(regexp_replace(coalesce(p_product_name, ''), '[[:space:]]+', ' ', 'g')))
    || chr(31)
    || lower(btrim(regexp_replace(coalesce(p_raw_ingredient_text, ''), '[[:space:]]+', ' ', 'g')))
  );
$$;

REVOKE ALL ON FUNCTION public.product_submission_fingerprint(TEXT, TEXT, TEXT)
  FROM PUBLIC, anon;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'product_submissions'
      AND column_name = 'submission_fingerprint'
  ) THEN
    ALTER TABLE public.product_submissions
      ADD COLUMN submission_fingerprint TEXT
      GENERATED ALWAYS AS (
        public.product_submission_fingerprint(
          brand_name,
          product_name,
          raw_ingredient_text
        )
      ) STORED;
  END IF;
END
$$;

DO $$
DECLARE
  v_remaining INTEGER;
BEGIN
  WITH ranked AS (
    SELECT
      id,
      status,
      row_number() OVER (
        PARTITION BY submitted_by, submission_fingerprint
        ORDER BY
          CASE status
            WHEN 'pending_human' THEN 6
            WHEN 'decision_ready' THEN 5
            WHEN 'batch_preparing' THEN 4
            WHEN 'verifying' THEN 3
            WHEN 'triaging' THEN 2
            WHEN 'received' THEN 1
            ELSE 0
          END DESC,
          created_at ASC,
          id ASC
      ) AS rn
    FROM public.product_submissions
    WHERE submitted_by IS NOT NULL
      AND submission_fingerprint IS NOT NULL
      AND status IN (
        'received', 'triaging', 'verifying', 'batch_preparing',
        'decision_ready', 'pending_human'
      )
  ),
  closed AS (
    UPDATE public.product_submissions ps
    SET status = 'duplicate',
        updated_at = now()
    FROM ranked r
    WHERE ps.id = r.id
      AND r.rn > 1
      AND ps.status = 'received'
    RETURNING ps.id
  )
  INSERT INTO public.submission_audit (submission_id, action, actor, payload)
  SELECT id, 'duplicate', 'migration:20261127000500', '{}'::jsonb
  FROM closed;

  SELECT count(*)::INTEGER INTO v_remaining
  FROM (
    SELECT 1
    FROM public.product_submissions
    WHERE submitted_by IS NOT NULL
      AND submission_fingerprint IS NOT NULL
      AND status IN (
        'received', 'triaging', 'verifying', 'batch_preparing',
        'decision_ready', 'pending_human'
      )
    GROUP BY submitted_by, submission_fingerprint
    HAVING count(*) > 1
  ) dups;

  IF v_remaining > 0 THEN
    RAISE EXCEPTION
      'cannot add unique open-submission fingerprint index: % in-flight duplicate group(s) remain',
      v_remaining;
  END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS product_submissions_submitter_fingerprint_open_uidx
  ON public.product_submissions (submitted_by, submission_fingerprint)
  WHERE submitted_by IS NOT NULL
    AND status IN (
      'received', 'triaging', 'verifying', 'batch_preparing',
      'decision_ready', 'pending_human'
    );

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

  FOR v_attempt IN 1..2 LOOP
    INSERT INTO product_submissions
      (submitted_by, brand_name, product_name, raw_ingredient_text)
    VALUES (v_user, v_brand, v_product, v_label)
    ON CONFLICT (submitted_by, submission_fingerprint)
      WHERE submitted_by IS NOT NULL
        AND status IN (
          'received', 'triaging', 'verifying', 'batch_preparing',
          'decision_ready', 'pending_human'
        )
    DO NOTHING
    RETURNING id INTO v_id;

    IF v_id IS NOT NULL THEN
      INSERT INTO submission_audit (submission_id, action, actor, payload)
      VALUES (v_id, 'submitted', v_user::TEXT, '{}'::jsonb);
      RETURN v_id;
    END IF;

    SELECT id INTO v_id
    FROM product_submissions
    WHERE submitted_by = v_user
      AND submission_fingerprint = public.product_submission_fingerprint(
        v_brand, v_product, v_label
      )
      AND status IN (
        'received', 'triaging', 'verifying', 'batch_preparing',
        'decision_ready', 'pending_human'
      )
    ORDER BY created_at, id
    LIMIT 1;

    IF v_id IS NOT NULL THEN
      RETURN v_id;
    END IF;
  END LOOP;

  RAISE EXCEPTION 'failed to submit product'
    USING ERRCODE = '40001';
END;
$$;

REVOKE ALL ON FUNCTION public.submit_product_submission(TEXT, TEXT, TEXT)
  FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.submit_product_submission(TEXT, TEXT, TEXT)
  TO authenticated;
