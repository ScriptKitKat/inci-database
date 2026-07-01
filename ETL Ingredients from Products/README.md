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

Useful judge overrides:

```bash
.venv/bin/ingredient-cleanup auto \
  --since 2026-06-30 \
  --model claude-sonnet-4-6 \
  --temperature 0.1 \
  --max-tokens 900
```

## Contents

- `src/inci_pipeline/curation/`: scoring, decisions, review stub, Anthropic batch judge.
- `src/inci_pipeline/sources/ingredient_verification.py`: OBF, PubChem, Wikidata, SpecialChem, INCIDecoder evidence lookups.
- `src/inci_pipeline/stages/curate_ingredient_names.py`: queue, deterministic curation, and apply flow.
- `supabase/migrations/20260630000100_ingredient_name_curation_pipeline.sql`: queue/evidence/decision/audit schema and RPCs.
- `supabase/manual_scripts/`: older one-off cleanup SQL scripts kept here for reference/manual recovery.
- `tests/`: focused tests for the cleanup ETL.
