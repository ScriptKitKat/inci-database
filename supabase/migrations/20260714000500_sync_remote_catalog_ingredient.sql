CREATE OR REPLACE FUNCTION sync_remote_catalog_ingredient(
  p_id         UUID,
  p_inci_name  TEXT,
  p_slug       TEXT
)
RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_id UUID;
BEGIN
  PERFORM assert_curator_or_service();
  IF p_id IS NULL OR nullif(trim(p_inci_name), '') IS NULL
      OR nullif(trim(p_slug), '') IS NULL THEN
    RAISE EXCEPTION 'remote catalog ingredient is incomplete';
  END IF;

  SELECT id INTO v_id
  FROM ingredients
  WHERE normalized_name = inci_normalize(p_inci_name);
  IF v_id IS NOT NULL THEN RETURN v_id; END IF;

  BEGIN
    INSERT INTO ingredients (id, inci_name, slug)
    VALUES (p_id, trim(p_inci_name), trim(p_slug))
    RETURNING id INTO v_id;
  EXCEPTION WHEN unique_violation THEN
    SELECT id INTO v_id
    FROM ingredients
    WHERE id = p_id OR normalized_name = inci_normalize(p_inci_name)
    ORDER BY (id = p_id) DESC
    LIMIT 1;
    IF v_id IS NULL THEN RAISE; END IF;
  END;
  RETURN v_id;
END;
$$;

REVOKE ALL ON FUNCTION sync_remote_catalog_ingredient(UUID, TEXT, TEXT)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION sync_remote_catalog_ingredient(UUID, TEXT, TEXT)
  TO service_role;
