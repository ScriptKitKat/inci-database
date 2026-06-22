-- Editorial content. Multi-language by design (UNIQUE on
-- (ingredient_id, language)). model_version is mandatory for any
-- LLM-generated row so drafts can be regenerated and audited.

CREATE TABLE ingredient_content (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_id   UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
  language        TEXT NOT NULL DEFAULT 'en',

  summary_short   TEXT,
  summary_long    TEXT,
  quick_facts     TEXT[],
  what_it_does    TEXT,

  status          editorial_status NOT NULL DEFAULT 'draft',
  model_version   TEXT,
  reviewed_by     TEXT,
  reviewed_at     TIMESTAMPTZ,

  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (ingredient_id, language)
);

CREATE INDEX content_status_idx     ON ingredient_content (status);
CREATE INDEX content_ingredient_idx ON ingredient_content (ingredient_id);
