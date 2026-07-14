-- Normalize ingredient details and editorial write-ups without losing data.
--
-- `ingredient_information.ingredient_id` and
-- `ingredient_writeups.ingredient_id` are the authoritative one-to-one links.
-- The two nullable ids on `ingredients` are convenient read pointers maintained
-- by triggers. They use ON DELETE SET NULL to avoid unsafe circular deletes.

CREATE TABLE ingredient_information (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_id          UUID NOT NULL UNIQUE
                           REFERENCES ingredients(id) ON DELETE CASCADE
                           DEFERRABLE INITIALLY DEFERRED,
  rating                 ingredient_rating,
  functions              TEXT[] NOT NULL DEFAULT '{}',
  cosing_information     JSONB NOT NULL DEFAULT '{}'::jsonb
                           CHECK (jsonb_typeof(cosing_information) = 'object'),
  additional_information JSONB NOT NULL DEFAULT '{}'::jsonb
                           CHECK (jsonb_typeof(additional_information) = 'object'),
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON COLUMN ingredient_information.cosing_information IS
  'Structured CosIng-style fields, e.g. description, cas_number, ec_number, iupac_name and ph_eur_name.';
COMMENT ON COLUMN ingredient_information.additional_information IS
  'Lossless home for legacy classification and safety fields not present in the public redesign.';

CREATE TABLE ingredient_writeups (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_id    UUID NOT NULL UNIQUE
                     REFERENCES ingredients(id) ON DELETE CASCADE
                     DEFERRABLE INITIALLY DEFERRED,
  quick_facts      TEXT[] NOT NULL DEFAULT '{}',
  summary          TEXT,
  details          TEXT,
  proof_articles   JSONB NOT NULL DEFAULT '[]'::jsonb
                     CHECK (jsonb_typeof(proof_articles) = 'array'),
  editorial_metadata JSONB NOT NULL DEFAULT '{}'::jsonb
                     CHECK (jsonb_typeof(editorial_metadata) = 'object'),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON COLUMN ingredient_writeups.proof_articles IS
  'Snapshot of supporting PubMed records; ingredient_sources remains the normalized provenance store.';

-- Parsing/audit fields do not belong on the core many-to-many relation, but
-- moving them here preserves every imported label token.
CREATE TABLE product_ingredient_metadata (
  product_ingredient_id UUID PRIMARY KEY
    REFERENCES product_ingredients(id) ON DELETE CASCADE,
  raw_inci_token        TEXT NOT NULL,
  is_matched            BOOLEAN NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE product_metadata (
  product_id             UUID PRIMARY KEY
    REFERENCES products(id) ON DELETE CASCADE,
  ingredient_fingerprint TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Build indexes before the data backfill. Supabase runs each migration in one
-- transaction, and PostgreSQL cannot CREATE INDEX while deferred trigger
-- events from the backfill are still pending.
CREATE INDEX ingredient_information_functions_gin
  ON ingredient_information USING GIN (functions);
CREATE INDEX ingredient_information_cosing_gin
  ON ingredient_information USING GIN (cosing_information);
CREATE INDEX ingredient_information_cas_idx
  ON ingredient_information ((cosing_information ->> 'cas_number'))
  WHERE cosing_information ? 'cas_number';
CREATE INDEX ingredient_writeups_articles_gin
  ON ingredient_writeups USING GIN (proof_articles);
CREATE INDEX product_ingredient_metadata_matched_idx
  ON product_ingredient_metadata (is_matched);

-- Enable RLS before the backfill. Supabase executes this migration in one
-- transaction, and ALTER TABLE cannot run while backfill trigger events are
-- pending.
ALTER TABLE ingredient_information ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_writeups ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_ingredient_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_metadata ENABLE ROW LEVEL SECURITY;

CREATE POLICY public_read_ingredient_information ON ingredient_information
  FOR SELECT USING (true);

CREATE POLICY public_read_published_writeups ON ingredient_writeups
  FOR SELECT USING (editorial_metadata ->> 'status' = 'published');

CREATE POLICY public_read_product_ingredient_metadata ON product_ingredient_metadata
  FOR SELECT USING (true);

-- The linked project has already removed ingredient_fingerprint, while a
-- freshly replayed local schema still has it. Dynamic SQL supports both states.
DO $$
DECLARE
  v_missing BOOLEAN;
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'products'
      AND column_name = 'ingredient_fingerprint'
  ) THEN
    EXECUTE $sql$
      INSERT INTO product_metadata (product_id, ingredient_fingerprint)
      SELECT id, ingredient_fingerprint
      FROM products
      WHERE ingredient_fingerprint IS NOT NULL
    $sql$;
    EXECUTE $sql$
      SELECT EXISTS (
        SELECT 1
        FROM products p
        WHERE p.ingredient_fingerprint IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM product_metadata m WHERE m.product_id = p.id
          )
      )
    $sql$ INTO v_missing;
    IF v_missing THEN
      RAISE EXCEPTION 'product fingerprint backfill is incomplete';
    END IF;
  END IF;
END $$;

ALTER TABLE ingredients
  ADD COLUMN ingredient_information_id UUID,
  ADD COLUMN ingredient_writeup_id UUID;

-- One information row per existing ingredient. JSONB is used so that the
-- migration is lossless even though the new public model is intentionally lean.
INSERT INTO ingredient_information (
  ingredient_id,
  rating,
  functions,
  cosing_information,
  additional_information,
  created_at,
  updated_at
)
SELECT
  i.id,
  i.rating,
  i.function_tags,
  jsonb_strip_nulls(jsonb_build_object(
    'cas_number', i.cas_number,
    'ec_number', i.ec_number,
    'iupac_name', i.iupac_name,
    'ph_eur_name', i.ph_eur_name
  )),
  jsonb_strip_nulls(jsonb_build_object(
    'skin_type_tags', i.skin_type_tag,
    'concern_tags', i.concern_tag,
    'is_restricted_eu', i.is_restricted_eu,
    'is_restricted_us', i.is_restricted_us,
    'is_comedogenic', i.is_comedogenic,
    'irritancy_level', i.irritancy_level
  )),
  i.created_at,
  i.updated_at
FROM ingredients i;

-- Create a write-up when editorial content or supporting articles exist.
WITH pubmed_articles AS (
  SELECT
    s.ingredient_id,
    jsonb_agg(
      jsonb_strip_nulls(jsonb_build_object(
        'source_id', s.id,
        'external_id', s.external_id,
        'url', s.url,
        'title', s.title,
        'raw_payload', s.raw_payload,
        'retrieved_at', s.retrieved_at
      ))
      ORDER BY s.retrieved_at, s.id
    ) AS articles
  FROM ingredient_sources s
  WHERE s.source_type = 'pubmed'
  GROUP BY s.ingredient_id
)
INSERT INTO ingredient_writeups (
  id,
  ingredient_id,
  quick_facts,
  summary,
  details,
  proof_articles,
  editorial_metadata,
  created_at,
  updated_at
)
SELECT
  COALESCE(c.id, gen_random_uuid()),
  COALESCE(c.ingredient_id, p.ingredient_id),
  COALESCE(c.quick_facts, '{}'),
  c.summary_short,
  c.summary_long,
  COALESCE(p.articles, '[]'::jsonb),
  CASE WHEN c.id IS NULL THEN '{}'::jsonb ELSE
    jsonb_strip_nulls(jsonb_build_object(
      'language', c.language,
      'status', c.status,
      'model_version', c.model_version,
      'reviewed_by', c.reviewed_by,
      'reviewed_at', c.reviewed_at,
      'what_it_does', c.what_it_does
    ))
  END,
  COALESCE(c.created_at, now()),
  COALESCE(c.updated_at, now())
FROM ingredient_content c
FULL OUTER JOIN pubmed_articles p ON p.ingredient_id = c.ingredient_id;

UPDATE ingredients i
SET ingredient_information_id = info.id
FROM ingredient_information info
WHERE info.ingredient_id = i.id;

UPDATE ingredients i
SET ingredient_writeup_id = w.id
FROM ingredient_writeups w
WHERE w.ingredient_id = i.id;

INSERT INTO product_ingredient_metadata (
  product_ingredient_id,
  raw_inci_token,
  is_matched
)
SELECT id, raw_inci_token, is_matched
FROM product_ingredients;

-- Abort the transaction rather than dropping old columns if any backfill is
-- incomplete. This is deliberately checked before the destructive phase.
DO $$
DECLARE
  v_ingredients BIGINT;
  v_information BIGINT;
  v_product_ingredients BIGINT;
  v_product_metadata BIGINT;
  v_expected_writeups BIGINT;
  v_writeups BIGINT;
BEGIN
  SELECT count(*) INTO v_ingredients FROM ingredients;
  SELECT count(*) INTO v_information FROM ingredient_information;
  SELECT count(*) INTO v_product_ingredients FROM product_ingredients;
  SELECT count(*) INTO v_product_metadata FROM product_ingredient_metadata;
  SELECT count(*) INTO v_expected_writeups
  FROM (
    SELECT ingredient_id FROM ingredient_content
    UNION
    SELECT ingredient_id FROM ingredient_sources WHERE source_type = 'pubmed'
  ) expected;
  SELECT count(*) INTO v_writeups FROM ingredient_writeups;

  IF v_ingredients <> v_information THEN
    RAISE EXCEPTION 'ingredient information backfill mismatch: % ingredients, % information rows',
      v_ingredients, v_information;
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ingredient_information info
    JOIN ingredients i ON i.id = info.ingredient_id
    WHERE i.ingredient_information_id IS DISTINCT FROM info.id
  ) THEN
    RAISE EXCEPTION 'ingredient_information_id pointer backfill is incomplete';
  END IF;

  IF v_product_ingredients <> v_product_metadata THEN
    RAISE EXCEPTION 'product ingredient metadata backfill mismatch: % links, % metadata rows',
      v_product_ingredients, v_product_metadata;
  END IF;

  IF v_expected_writeups <> v_writeups THEN
    RAISE EXCEPTION 'write-up backfill mismatch: % expected, % write-up rows',
      v_expected_writeups, v_writeups;
  END IF;

  IF EXISTS (
    SELECT 1
    FROM product_ingredients pi
    JOIN product_ingredient_metadata m ON m.product_ingredient_id = pi.id
    WHERE m.raw_inci_token IS DISTINCT FROM pi.raw_inci_token
       OR m.is_matched IS DISTINCT FROM pi.is_matched
  ) THEN
    RAISE EXCEPTION 'product ingredient metadata values differ from their source rows';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ingredient_content c
    JOIN ingredient_writeups w ON w.id = c.id
    WHERE w.ingredient_id IS DISTINCT FROM c.ingredient_id
       OR w.quick_facts IS DISTINCT FROM c.quick_facts
       OR w.summary IS DISTINCT FROM c.summary_short
       OR w.details IS DISTINCT FROM c.summary_long
       OR w.editorial_metadata ->> 'what_it_does' IS DISTINCT FROM c.what_it_does
  ) THEN
    RAISE EXCEPTION 'editorial values differ from their source rows';
  END IF;
END $$;

ALTER TABLE ingredients
  ADD CONSTRAINT ingredients_information_fk
    FOREIGN KEY (ingredient_information_id)
    REFERENCES ingredient_information(id)
    DEFERRABLE INITIALLY DEFERRED,
  ADD CONSTRAINT ingredients_writeup_fk
    FOREIGN KEY (ingredient_writeup_id)
    REFERENCES ingredient_writeups(id)
    ON DELETE SET NULL
    DEFERRABLE INITIALLY DEFERRED;

CREATE TRIGGER trg_ingredient_information_updated
  BEFORE UPDATE ON ingredient_information
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_ingredient_writeups_updated
  BEFORE UPDATE ON ingredient_writeups
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE FUNCTION sync_ingredient_detail_pointer()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF TG_OP = 'UPDATE' AND OLD.ingredient_id IS DISTINCT FROM NEW.ingredient_id THEN
    IF TG_TABLE_NAME = 'ingredient_information' THEN
      UPDATE ingredients SET ingredient_information_id = NULL
      WHERE id = OLD.ingredient_id AND ingredient_information_id = OLD.id;
    ELSE
      UPDATE ingredients SET ingredient_writeup_id = NULL
      WHERE id = OLD.ingredient_id AND ingredient_writeup_id = OLD.id;
    END IF;
  END IF;

  IF TG_TABLE_NAME = 'ingredient_information' THEN
    UPDATE ingredients SET ingredient_information_id = NEW.id
    WHERE id = NEW.ingredient_id;
  ELSE
    UPDATE ingredients SET ingredient_writeup_id = NEW.id
    WHERE id = NEW.ingredient_id;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sync_ingredient_information_pointer
  AFTER INSERT OR UPDATE OF ingredient_id ON ingredient_information
  FOR EACH ROW EXECUTE FUNCTION sync_ingredient_detail_pointer();

CREATE TRIGGER trg_sync_ingredient_writeup_pointer
  AFTER INSERT OR UPDATE OF ingredient_id ON ingredient_writeups
  FOR EACH ROW EXECUTE FUNCTION sync_ingredient_detail_pointer();

CREATE OR REPLACE FUNCTION ensure_ingredient_information()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO ingredient_information (ingredient_id)
  VALUES (NEW.id)
  ON CONFLICT (ingredient_id) DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_ensure_ingredient_information
  AFTER INSERT ON ingredients
  FOR EACH ROW EXECUTE FUNCTION ensure_ingredient_information();

-- Destructive phase: all values below have been copied and checked above.
DROP TRIGGER IF EXISTS trg_ingredient_content_updated ON ingredient_content;
DROP TABLE ingredient_content;

ALTER TABLE ingredients
  DROP COLUMN rating,
  DROP COLUMN function_tags,
  DROP COLUMN skin_type_tag,
  DROP COLUMN concern_tag,
  DROP COLUMN cas_number,
  DROP COLUMN ec_number,
  DROP COLUMN iupac_name,
  DROP COLUMN ph_eur_name,
  DROP COLUMN is_restricted_eu,
  DROP COLUMN is_restricted_us,
  DROP COLUMN is_comedogenic,
  DROP COLUMN irritancy_level;

ALTER TABLE product_ingredients
  DROP COLUMN raw_inci_token,
  DROP COLUMN is_matched;

-- The live project already removed this implementation-only column; this
-- keeps fresh local databases and the linked database convergent.
ALTER TABLE products
  DROP COLUMN IF EXISTS ingredient_fingerprint;

-- Keep the curation RPC compatible with the normalized tables.
CREATE OR REPLACE FUNCTION apply_ingredient_curation_decision(p_decision_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
  d ingredient_curation_decisions%ROWTYPE;
  v_source_name TEXT;
  v_target_name TEXT;
  v_alias TEXT;
  v_before JSONB;
  v_after JSONB;
BEGIN
  SELECT * INTO d
  FROM ingredient_curation_decisions
  WHERE id = p_decision_id
  FOR UPDATE;

  IF d.id IS NULL THEN RETURN 'decision not found'; END IF;
  IF d.review_status NOT IN ('not_required', 'approved') THEN
    RETURN format('decision %s is not apply-eligible: %s', d.id, d.review_status);
  END IF;

  IF d.confidence < 0.90 AND d.review_status <> 'approved' THEN
    UPDATE ingredient_curation_decisions SET review_status = 'pending_human' WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now() WHERE id = d.queue_id;
    RETURN 'decision confidence below automatic apply threshold';
  END IF;

  SELECT jsonb_build_object(
    'decision', to_jsonb(d),
    'source_ingredient', (SELECT to_jsonb(i) FROM ingredients i WHERE i.id = d.source_ingredient_id),
    'source_information', (SELECT to_jsonb(x) FROM ingredient_information x WHERE x.ingredient_id = d.source_ingredient_id),
    'source_writeup', (SELECT to_jsonb(x) FROM ingredient_writeups x WHERE x.ingredient_id = d.source_ingredient_id),
    'target_ingredient', (SELECT to_jsonb(i) FROM ingredients i WHERE i.id = d.target_ingredient_id)
  ) INTO v_before;

  IF d.decision = 'keep' THEN
    UPDATE ingredient_curation_decisions SET review_status = 'applied', applied_at = now() WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'kept', processed_at = now(), locked_at = NULL WHERE id = d.queue_id;
    INSERT INTO ingredient_curation_apply_audit
      (decision_id, action, source_ingredient_id, target_ingredient_id, before_payload, after_payload)
    VALUES (d.id, 'keep', d.source_ingredient_id, d.target_ingredient_id, v_before, '{}'::jsonb);
    RETURN 'kept';
  END IF;

  IF d.decision IN ('reject_or_quarantine', 'needs_human') THEN
    UPDATE ingredient_curation_decisions SET review_status = 'pending_human' WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now(), locked_at = NULL WHERE id = d.queue_id;
    RETURN 'pending_human';
  END IF;

  IF d.source_ingredient_id IS NULL OR d.target_ingredient_id IS NULL THEN
    UPDATE ingredient_curation_decisions SET review_status = 'pending_human' WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now(), locked_at = NULL WHERE id = d.queue_id;
    RETURN 'source or target ingredient missing';
  END IF;

  SELECT inci_name INTO v_source_name FROM ingredients WHERE id = d.source_ingredient_id;
  SELECT inci_name INTO v_target_name FROM ingredients WHERE id = d.target_ingredient_id;
  IF v_source_name IS NULL OR v_target_name IS NULL THEN
    UPDATE ingredient_curation_decisions SET review_status = 'pending_human' WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now(), locked_at = NULL WHERE id = d.queue_id;
    RETURN 'source or target ingredient row not found';
  END IF;

  UPDATE product_ingredients
  SET ingredient_id = d.target_ingredient_id
  WHERE ingredient_id = d.source_ingredient_id;

  INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
  VALUES (
    d.target_ingredient_id, v_source_name,
    CASE WHEN d.decision = 'merge_into_existing' THEN 'typo' ELSE 'synonym' END::alias_type,
    'en', 'manual'
  )
  ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

  FOREACH v_alias IN ARRAY d.aliases_to_add LOOP
    INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
    VALUES (d.target_ingredient_id, v_alias, 'synonym', 'en', 'manual')
    ON CONFLICT (ingredient_id, alias, language) DO NOTHING;
  END LOOP;

  INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
  SELECT d.target_ingredient_id, a.alias, a.alias_type, a.language, a.source
  FROM ingredient_aliases a WHERE a.ingredient_id = d.source_ingredient_id
  ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

  INSERT INTO ingredient_sources (ingredient_id, source_type, external_id, url, title, raw_payload)
  SELECT d.target_ingredient_id, s.source_type, s.external_id, s.url, s.title, s.raw_payload
  FROM ingredient_sources s WHERE s.ingredient_id = d.source_ingredient_id
  ON CONFLICT (ingredient_id, source_type, external_id) DO NOTHING;

  INSERT INTO ingredient_curation_queue (ingredient_id, priority, notes)
  SELECT d.target_ingredient_id, q.priority, q.notes
  FROM ingredient_curation_queue q WHERE q.ingredient_id = d.source_ingredient_id
  ON CONFLICT (ingredient_id) DO NOTHING;

  -- Promote non-conflicting information and retain the complete losing row as
  -- an audit snapshot when values differ.
  UPDATE ingredient_information target
  SET rating = COALESCE(target.rating, source.rating),
      functions = ARRAY(
        SELECT DISTINCT value
        FROM unnest(target.functions || source.functions) AS value
        ORDER BY value
      ),
      cosing_information = source.cosing_information || target.cosing_information,
      additional_information = target.additional_information || jsonb_build_object(
        'merged_information',
        COALESCE(target.additional_information -> 'merged_information', '[]'::jsonb)
          || jsonb_build_array(to_jsonb(source) - 'id' - 'ingredient_id')
      )
  FROM ingredient_information source
  WHERE target.ingredient_id = d.target_ingredient_id
    AND source.ingredient_id = d.source_ingredient_id;

  IF EXISTS (SELECT 1 FROM ingredient_writeups WHERE ingredient_id = d.target_ingredient_id) THEN
    UPDATE ingredient_writeups target
    SET quick_facts = CASE WHEN cardinality(target.quick_facts) > 0
                       THEN target.quick_facts ELSE source.quick_facts END,
        summary = COALESCE(target.summary, source.summary),
        details = COALESCE(target.details, source.details),
        proof_articles = target.proof_articles || source.proof_articles,
        editorial_metadata = target.editorial_metadata || jsonb_build_object(
          'merged_writeups',
          COALESCE(target.editorial_metadata -> 'merged_writeups', '[]'::jsonb)
            || jsonb_build_array(to_jsonb(source) - 'id' - 'ingredient_id')
        )
    FROM ingredient_writeups source
    WHERE target.ingredient_id = d.target_ingredient_id
      AND source.ingredient_id = d.source_ingredient_id;
  ELSE
    UPDATE ingredient_writeups
    SET ingredient_id = d.target_ingredient_id
    WHERE ingredient_id = d.source_ingredient_id;
  END IF;

  DELETE FROM ingredients WHERE id = d.source_ingredient_id;

  UPDATE ingredient_curation_decisions
  SET review_status = 'applied', applied_at = now() WHERE id = d.id;
  UPDATE ingredient_name_curation_queue
  SET queue_status = 'applied', processed_at = now(), locked_at = NULL WHERE id = d.queue_id;

  SELECT jsonb_build_object(
    'decision_id', d.id,
    'target_ingredient', (SELECT to_jsonb(i) FROM ingredients i WHERE i.id = d.target_ingredient_id),
    'target_information', (SELECT to_jsonb(x) FROM ingredient_information x WHERE x.ingredient_id = d.target_ingredient_id),
    'target_writeup', (SELECT to_jsonb(x) FROM ingredient_writeups x WHERE x.ingredient_id = d.target_ingredient_id)
  ) INTO v_after;

  INSERT INTO ingredient_curation_apply_audit
    (decision_id, action, source_ingredient_id, target_ingredient_id, before_payload, after_payload)
  VALUES (d.id, d.decision, d.source_ingredient_id, d.target_ingredient_id,
          v_before, COALESCE(v_after, '{}'::jsonb));

  RETURN format('%s applied: %s -> %s', d.decision, v_source_name, v_target_name);
END;
$$;

-- The normalized-name uniqueness constraint means duplicate groups should not
-- normally exist. Replace the legacy implementation so it cannot reference
-- columns removed above; curation merges use apply_ingredient_curation_decision.
CREATE OR REPLACE FUNCTION merge_duplicate_ingredients(
  target_normalized_name TEXT,
  canonical_inci_name TEXT,
  preferred_slug TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
  v_id UUID;
  v_count INTEGER;
BEGIN
  SELECT min(id::text)::uuid, count(*) INTO v_id, v_count
  FROM ingredients
  WHERE normalized_name = target_normalized_name;

  IF v_id IS NULL THEN
    RETURN format('no rows with normalized_name=%L found', target_normalized_name);
  END IF;
  IF v_count > 1 THEN
    RAISE EXCEPTION 'unexpected duplicate group; use reviewed curation decisions to merge without data loss';
  END IF;

  UPDATE ingredients
  SET inci_name = canonical_inci_name, slug = preferred_slug
  WHERE id = v_id;
  RETURN format('one row exists, normalized to %L', canonical_inci_name);
END;
$$;
