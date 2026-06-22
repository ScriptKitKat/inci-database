-- Audit log for pipeline runs. Lets stages check "did I already
-- complete successfully today?" before redoing expensive work.

CREATE TABLE ingestion_runs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stage         TEXT NOT NULL,
  started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at   TIMESTAMPTZ,
  status        TEXT NOT NULL DEFAULT 'running',
  rows_in       INTEGER,
  rows_upserted INTEGER,
  error         TEXT,
  metadata      JSONB
);

CREATE INDEX ingestion_runs_stage_idx ON ingestion_runs (stage, started_at DESC);
