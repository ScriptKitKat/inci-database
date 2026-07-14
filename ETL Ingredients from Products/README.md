# ETL Ingredients from Products

Standalone ETL for cleaning product-derived ingredient rows after bulk import.
The root `pipeline/` folder stays focused on seeding/importing data; this folder
owns normalized-name cleanup, source verification, LLM judging, and apply/audit.

## Setup

```bash
cd "ETL Ingredients from Products"
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Put Supabase and Claude credentials in `.env`:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
ANTHROPIC_API_KEY=...
```

## Run

Apply the migration from this folder before the first run:

```bash
supabase db push
```

Clean ingredients created on June 30, 2026:

```bash
.venv/bin/ingredient-cleanup auto --since 2026-06-30
```

`auto` queues the date window, then drains the cleanup queue in batches until no
pending rows remain. `--limit` controls the per-batch claim size, not the total
number of ingredients to process.

Useful judge overrides:

```bash
.venv/bin/ingredient-cleanup auto \
  --since 2026-06-30 \
  --limit 1000 \
  --clear-queue-on-finish \
  --model claude-sonnet-4-6 \
  --temperature 0.1 \
  --max-tokens 900
```

The queue is operational state. To clear finished queue rows later without
deleting candidates, evidence, decisions, or audit records:

```bash
.venv/bin/ingredient-cleanup clear-queue --since 2026-06-30
```

Only terminal queue rows are deleted: `applied`, `kept`, `pending_human`, and
`failed`. Pending or processing rows are preserved.

## Resume After An Interrupted Run

If a run fails after deterministic curation, resume the same `run_id` instead of
starting over:

```bash
.venv/bin/ingredient-cleanup resume --run-id <curation_run_id>
```

If you did not save the run id, find the latest runs in Supabase:

```sql
select id, started_at, rows_in, rows_decided, status, error
from ingredient_name_curation_runs
order by started_at desc
limit 5;
```

`resume` reuses an already-submitted Anthropic batch when one exists. If the
failure happened before the batch reached Anthropic, it submits the pending LLM
items and then continues to apply eligible decisions.

## Contents

- `src/inci_pipeline/curation/`: scoring, decisions, review stub, Anthropic batch judge.
- `src/inci_pipeline/sources/ingredient_verification.py`: OBF, PubChem, Wikidata, SpecialChem, INCIDecoder evidence lookups.
- `src/inci_pipeline/stages/curate_ingredient_names.py`: queue, deterministic curation, and apply flow.
- `supabase/migrations/20260630000100_ingredient_name_curation_pipeline.sql`: queue/evidence/decision/audit schema and RPCs.
- `supabase/manual_scripts/`: older one-off cleanup SQL scripts kept here for reference/manual recovery.
- `tests/`: focused tests for the cleanup ETL.
