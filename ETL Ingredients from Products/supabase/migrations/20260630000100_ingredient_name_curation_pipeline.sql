-- Normalized ingredient-name curation pipeline.
--
-- This is intentionally review-first: incoming ingredient rows are queued,
-- deterministic/LLM stages write evidence and decisions, and only the
-- explicit apply RPC mutates canonical data.

CREATE TABLE ingredient_name_curation_queue (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_id   UUID UNIQUE REFERENCES ingredients(id) ON DELETE SET NULL,
  normalized_name TEXT NOT NULL,
  queue_status    TEXT NOT NULL DEFAULT 'pending'
    CHECK (queue_status IN (
      'pending',
      'processing',
      'decision_ready',
      'pending_human',
      'applied',
      'kept',
      'failed'
    )),
  queued_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  locked_at       TIMESTAMPTZ,
  processed_at    TIMESTAMPTZ,
  last_error      TEXT,
  attempt_count   INTEGER NOT NULL DEFAULT 0,
  metadata        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX ingredient_name_curation_queue_status_idx
  ON ingredient_name_curation_queue (queue_status, queued_at);

CREATE INDEX ingredient_name_curation_queue_normalized_idx
  ON ingredient_name_curation_queue (normalized_name);

CREATE TABLE ingredient_name_curation_runs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_type        TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'running'
    CHECK (status IN ('running', 'success', 'failed')),
  started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at     TIMESTAMPTZ,
  rows_in         INTEGER NOT NULL DEFAULT 0,
  rows_decided    INTEGER NOT NULL DEFAULT 0,
  rows_applied    INTEGER NOT NULL DEFAULT 0,
  config          JSONB NOT NULL DEFAULT '{}'::jsonb,
  error           TEXT
);

CREATE INDEX ingredient_name_curation_runs_status_idx
  ON ingredient_name_curation_runs (run_type, started_at DESC);

CREATE TABLE ingredient_name_candidates (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES ingredient_name_curation_runs(id) ON DELETE CASCADE,
  queue_id              UUID REFERENCES ingredient_name_curation_queue(id) ON DELETE SET NULL,
  source_ingredient_id  UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  inci_name             TEXT NOT NULL,
  normalized_name       TEXT NOT NULL,
  ingredient_created_at TIMESTAMPTZ,
  proposed_status       TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (run_id, source_ingredient_id)
);

CREATE INDEX ingredient_name_candidates_run_idx
  ON ingredient_name_candidates (run_id);

CREATE INDEX ingredient_name_candidates_normalized_idx
  ON ingredient_name_candidates (normalized_name);

CREATE TABLE ingredient_name_evidence (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES ingredient_name_curation_runs(id) ON DELETE CASCADE,
  candidate_id          UUID NOT NULL REFERENCES ingredient_name_candidates(id) ON DELETE CASCADE,
  source                TEXT NOT NULL,
  lookup_type           TEXT NOT NULL,
  found                 BOOLEAN NOT NULL DEFAULT false,
  canonical_name        TEXT,
  normalized_canonical  TEXT,
  url                   TEXT,
  confidence            REAL NOT NULL DEFAULT 0,
  raw_payload           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ingredient_name_evidence_candidate_idx
  ON ingredient_name_evidence (candidate_id);

CREATE INDEX ingredient_name_evidence_found_idx
  ON ingredient_name_evidence (source, found);

CREATE TABLE ingredient_name_edges (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                   UUID NOT NULL REFERENCES ingredient_name_curation_runs(id) ON DELETE CASCADE,
  candidate_id             UUID NOT NULL REFERENCES ingredient_name_candidates(id) ON DELETE CASCADE,
  source_ingredient_id     UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  target_ingredient_id     UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  source_normalized_name   TEXT NOT NULL,
  target_normalized_name   TEXT NOT NULL,
  relationship_type        TEXT NOT NULL,
  pg_trgm_similarity       REAL,
  edit_distance            INTEGER,
  token_overlap            REAL,
  score_margin             REAL,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ingredient_name_edges_candidate_idx
  ON ingredient_name_edges (candidate_id);

CREATE INDEX ingredient_name_edges_target_idx
  ON ingredient_name_edges (target_ingredient_id);

CREATE TABLE ingredient_llm_batches (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES ingredient_name_curation_runs(id) ON DELETE CASCADE,
  anthropic_batch_id    TEXT UNIQUE,
  status                TEXT NOT NULL DEFAULT 'created'
    CHECK (status IN ('created', 'submitted', 'processing', 'ended', 'failed', 'retrieved')),
  request_count         INTEGER NOT NULL DEFAULT 0,
  succeeded_count       INTEGER NOT NULL DEFAULT 0,
  errored_count         INTEGER NOT NULL DEFAULT 0,
  submitted_at          TIMESTAMPTZ,
  retrieved_at          TIMESTAMPTZ,
  raw_payload           JSONB NOT NULL DEFAULT '{}'::jsonb,
  error                 TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ingredient_llm_batch_items (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id              UUID NOT NULL REFERENCES ingredient_llm_batches(id) ON DELETE CASCADE,
  candidate_id          UUID REFERENCES ingredient_name_candidates(id) ON DELETE CASCADE,
  edge_id               UUID REFERENCES ingredient_name_edges(id) ON DELETE CASCADE,
  custom_id             TEXT NOT NULL,
  request_payload       JSONB NOT NULL,
  response_payload      JSONB,
  status                TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'submitted', 'succeeded', 'errored')),
  error                 TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (batch_id, custom_id)
);

CREATE INDEX ingredient_llm_batch_items_candidate_idx
  ON ingredient_llm_batch_items (candidate_id);

CREATE TABLE ingredient_curation_decisions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES ingredient_name_curation_runs(id) ON DELETE CASCADE,
  queue_id              UUID REFERENCES ingredient_name_curation_queue(id) ON DELETE SET NULL,
  candidate_id          UUID NOT NULL REFERENCES ingredient_name_candidates(id) ON DELETE CASCADE,
  source_ingredient_id  UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  target_ingredient_id  UUID REFERENCES ingredients(id) ON DELETE SET NULL,
  decision              TEXT NOT NULL
    CHECK (decision IN (
      'keep',
      'merge_into_existing',
      'alias_to_existing',
      'reject_or_quarantine',
      'needs_human'
    )),
  review_status         TEXT NOT NULL DEFAULT 'not_required'
    CHECK (review_status IN (
      'not_required',
      'pending_human',
      'approved',
      'rejected',
      'applied'
    )),
  decision_source       TEXT NOT NULL,
  canonical_inci_name   TEXT,
  aliases_to_add        TEXT[] NOT NULL DEFAULT '{}',
  confidence            REAL NOT NULL DEFAULT 0,
  reason                TEXT NOT NULL,
  applied_at            TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (run_id, candidate_id, decision_source)
);

CREATE INDEX ingredient_curation_decisions_run_idx
  ON ingredient_curation_decisions (run_id);

CREATE INDEX ingredient_curation_decisions_review_idx
  ON ingredient_curation_decisions (review_status, decision);

CREATE TABLE ingredient_curation_apply_audit (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id           UUID NOT NULL REFERENCES ingredient_curation_decisions(id) ON DELETE CASCADE,
  action                TEXT NOT NULL,
  source_ingredient_id  UUID,
  target_ingredient_id  UUID,
  before_payload        JSONB NOT NULL DEFAULT '{}'::jsonb,
  after_payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
  applied_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION enqueue_ingredient_name_curation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO ingredient_name_curation_queue (ingredient_id, normalized_name)
  VALUES (NEW.id, NEW.normalized_name)
  ON CONFLICT (ingredient_id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enqueue_ingredient_name_curation ON ingredients;
CREATE TRIGGER trg_enqueue_ingredient_name_curation
  AFTER INSERT ON ingredients
  FOR EACH ROW EXECUTE FUNCTION enqueue_ingredient_name_curation();

CREATE OR REPLACE FUNCTION enqueue_ingredient_name_curation_window(
  p_since TIMESTAMPTZ,
  p_until TIMESTAMPTZ
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
  v_count INTEGER;
BEGIN
  INSERT INTO ingredient_name_curation_queue (ingredient_id, normalized_name, metadata)
  SELECT i.id, i.normalized_name, jsonb_build_object('backfill', true)
  FROM ingredients i
  WHERE i.created_at >= p_since
    AND i.created_at < p_until
  ON CONFLICT (ingredient_id) DO NOTHING;

  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END;
$$;

CREATE OR REPLACE FUNCTION claim_ingredient_name_curation_queue(p_limit INTEGER)
RETURNS TABLE (
  queue_id UUID,
  ingredient_id UUID,
  inci_name TEXT,
  normalized_name TEXT,
  ingredient_created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH claimed AS (
    SELECT q.id
    FROM ingredient_name_curation_queue q
    WHERE q.queue_status = 'pending'
      AND q.ingredient_id IS NOT NULL
    ORDER BY q.queued_at, q.id
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED
  ),
  updated AS (
    UPDATE ingredient_name_curation_queue q
    SET queue_status = 'processing',
        locked_at = now(),
        attempt_count = attempt_count + 1,
        last_error = NULL
    FROM claimed
    WHERE q.id = claimed.id
    RETURNING q.id, q.ingredient_id, q.normalized_name
  )
  SELECT
    u.id AS queue_id,
    i.id AS ingredient_id,
    i.inci_name,
    u.normalized_name,
    i.created_at AS ingredient_created_at
  FROM updated u
  JOIN ingredients i ON i.id = u.ingredient_id;
END;
$$;

CREATE OR REPLACE FUNCTION fail_ingredient_name_curation_queue(
  p_queue_id UUID,
  p_error TEXT,
  p_max_attempts INTEGER DEFAULT 3
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE ingredient_name_curation_queue
  SET queue_status = CASE WHEN attempt_count >= p_max_attempts THEN 'failed' ELSE 'pending' END,
      locked_at = NULL,
      last_error = left(p_error, 2000)
  WHERE id = p_queue_id;
END;
$$;

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

  IF d.id IS NULL THEN
    RETURN 'decision not found';
  END IF;

  IF d.review_status NOT IN ('not_required', 'approved') THEN
    RETURN format('decision %s is not apply-eligible: %s', d.id, d.review_status);
  END IF;

  IF d.confidence < 0.90 AND d.review_status <> 'approved' THEN
    UPDATE ingredient_curation_decisions
    SET review_status = 'pending_human'
    WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now()
    WHERE id = d.queue_id;
    RETURN 'decision confidence below automatic apply threshold';
  END IF;

  SELECT to_jsonb(src) INTO v_before
  FROM (
    SELECT
      d.*,
      (SELECT to_jsonb(i) FROM ingredients i WHERE i.id = d.source_ingredient_id) AS source_ingredient,
      (SELECT to_jsonb(i) FROM ingredients i WHERE i.id = d.target_ingredient_id) AS target_ingredient
  ) src;

  IF d.decision = 'keep' THEN
    UPDATE ingredient_curation_decisions
    SET review_status = 'applied', applied_at = now()
    WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'kept', processed_at = now(), locked_at = NULL
    WHERE id = d.queue_id;
    INSERT INTO ingredient_curation_apply_audit (
      decision_id, action, source_ingredient_id, target_ingredient_id, before_payload, after_payload
    )
    VALUES (d.id, 'keep', d.source_ingredient_id, d.target_ingredient_id, v_before, '{}'::jsonb);
    RETURN 'kept';
  END IF;

  IF d.decision IN ('reject_or_quarantine', 'needs_human') THEN
    UPDATE ingredient_curation_decisions
    SET review_status = 'pending_human'
    WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now(), locked_at = NULL
    WHERE id = d.queue_id;
    RETURN 'pending_human';
  END IF;

  IF d.source_ingredient_id IS NULL OR d.target_ingredient_id IS NULL THEN
    UPDATE ingredient_curation_decisions
    SET review_status = 'pending_human'
    WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now(), locked_at = NULL
    WHERE id = d.queue_id;
    RETURN 'source or target ingredient missing';
  END IF;

  SELECT inci_name INTO v_source_name FROM ingredients WHERE id = d.source_ingredient_id;
  SELECT inci_name INTO v_target_name FROM ingredients WHERE id = d.target_ingredient_id;

  IF v_source_name IS NULL OR v_target_name IS NULL THEN
    UPDATE ingredient_curation_decisions
    SET review_status = 'pending_human'
    WHERE id = d.id;
    UPDATE ingredient_name_curation_queue
    SET queue_status = 'pending_human', processed_at = now(), locked_at = NULL
    WHERE id = d.queue_id;
    RETURN 'source or target ingredient row not found';
  END IF;

  UPDATE product_ingredients
  SET ingredient_id = d.target_ingredient_id,
      is_matched = true
  WHERE ingredient_id = d.source_ingredient_id;

  INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
  VALUES (
    d.target_ingredient_id,
    v_source_name,
    CASE WHEN d.decision = 'merge_into_existing' THEN 'typo' ELSE 'synonym' END::alias_type,
    'en',
    'manual'
  )
  ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

  FOREACH v_alias IN ARRAY d.aliases_to_add
  LOOP
    INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
    VALUES (d.target_ingredient_id, v_alias, 'synonym', 'en', 'manual')
    ON CONFLICT (ingredient_id, alias, language) DO NOTHING;
  END LOOP;

  INSERT INTO ingredient_aliases (ingredient_id, alias, alias_type, language, source)
  SELECT d.target_ingredient_id, a.alias, a.alias_type, a.language, a.source
  FROM ingredient_aliases a
  WHERE a.ingredient_id = d.source_ingredient_id
  ON CONFLICT (ingredient_id, alias, language) DO NOTHING;

  INSERT INTO ingredient_sources (ingredient_id, source_type, external_id, url, title, raw_payload)
  SELECT d.target_ingredient_id, s.source_type, s.external_id, s.url, s.title, s.raw_payload
  FROM ingredient_sources s
  WHERE s.ingredient_id = d.source_ingredient_id
  ON CONFLICT (ingredient_id, source_type, external_id) DO NOTHING;

  INSERT INTO ingredient_curation_queue (ingredient_id, priority, notes)
  SELECT d.target_ingredient_id, q.priority, q.notes
  FROM ingredient_curation_queue q
  WHERE q.ingredient_id = d.source_ingredient_id
  ON CONFLICT (ingredient_id) DO NOTHING;

  INSERT INTO ingredient_content
    (ingredient_id, language, summary_short, summary_long, quick_facts, what_it_does,
     status, model_version, reviewed_by, reviewed_at)
  SELECT d.target_ingredient_id, c.language, c.summary_short, c.summary_long, c.quick_facts, c.what_it_does,
         c.status, c.model_version, c.reviewed_by, c.reviewed_at
  FROM ingredient_content c
  WHERE c.ingredient_id = d.source_ingredient_id
  ON CONFLICT (ingredient_id, language) DO NOTHING;

  DELETE FROM ingredients
  WHERE id = d.source_ingredient_id;

  UPDATE ingredient_curation_decisions
  SET review_status = 'applied', applied_at = now()
  WHERE id = d.id;

  UPDATE ingredient_name_curation_queue
  SET queue_status = 'applied', processed_at = now(), locked_at = NULL
  WHERE id = d.queue_id;

  SELECT to_jsonb(dst) INTO v_after
  FROM (
    SELECT
      d.id AS decision_id,
      d.target_ingredient_id,
      (SELECT to_jsonb(i) FROM ingredients i WHERE i.id = d.target_ingredient_id) AS target_ingredient
  ) dst;

  INSERT INTO ingredient_curation_apply_audit (
    decision_id, action, source_ingredient_id, target_ingredient_id, before_payload, after_payload
  )
  VALUES (d.id, d.decision, d.source_ingredient_id, d.target_ingredient_id, v_before, coalesce(v_after, '{}'::jsonb));

  RETURN format('%s applied: %s -> %s', d.decision, v_source_name, v_target_name);
END;
$$;

ALTER TABLE ingredient_name_curation_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_name_curation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_name_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_name_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_name_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_llm_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_llm_batch_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_curation_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_curation_apply_audit ENABLE ROW LEVEL SECURITY;
