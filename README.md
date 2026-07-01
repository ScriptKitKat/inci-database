# inci-database

Schema + data pipeline for an INCIDecoder-style skincare ingredient database, backed by Supabase. The deliverable is migrations plus a Python pipeline — no application layer yet.

See `/Users/PriscillaYe/.claude/plans/you-are-an-expert-zippy-meerkat.md` for the full design rationale.

## Layout

```
inci-database/
  supabase/migrations/   # 11 SQL files, numbered to run in order
  pipeline/              # Python pipeline (uv/pip installable)
    src/inci_pipeline/
      sources/           # CosIng, PubChem, PubMed, Open Beauty Facts clients
      stages/            # 7 pipeline stages, each callable independently
      matching/          # token -> ingredient resolver (RPCs into Postgres)
      llm/               # Claude wrapper + prompt templates
    tests/
  data/
    raw/                 # CosIng + OBF dumps land here (gitignored)
    manifest.json        # checksums and source URLs
  .github/workflows/     # weekly cron + PR test workflow
```

## Apply the schema

Requires the [Supabase CLI](https://supabase.com/docs/guides/cli).

```bash
cd inci-database
supabase link --project-ref xwdmtipxfgcxfemnizie
supabase db push
```

To reset and reapply during development:

```bash
supabase db reset
supabase db push
```

## Run the pipeline

```bash
cd pipeline
cp .env.example .env
# fill in SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY, NCBI_API_KEY

# acquire source data
#  - OBF taxonomy -> data/raw/ingredients-cosing-obf.txt
#       curl -L -o ../data/raw/ingredients-cosing-obf.txt \
#         https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/main/taxonomies/beauty/ingredients-cosing-obf.txt
#  - OBF dump     -> data/raw/openbeautyfacts-products.jsonl.gz
#       curl -L -o ../data/raw/openbeautyfacts-products.jsonl.gz \
#         https://world.openbeautyfacts.org/data/openbeautyfacts-products.jsonl.gz

# first time: creates pipeline/.venv and installs deps
make install

# full pipeline (~ hours, mostly PubMed + Claude)
make seed

# or a single stage
inci-pipeline run obf-taxonomy
inci-pipeline run wikidata
inci-pipeline run pubchem
inci-pipeline run obf-aliases
inci-pipeline run pubmed
inci-pipeline run editorial
inci-pipeline run classify
inci-pipeline run products

# quick sanity check against the live db
inci-pipeline match "salycilic acid"   # typo, should still hit Salicylic Acid
```

## Stages

| #   | Stage | Reads | Writes |
|-----|-------|-------|--------|
| 1   | obf-taxonomy | OBF `ingredients.txt` | `ingredients`, `ingredient_aliases` (synonyms + translations), `ingredient_sources` (wikidata id) |
| 1b  | wikidata | `ingredients` with CAS | `ingredients.ec_number` (when missing), `ingredient_sources` (EC/InChI/formula) |
| 2   | pubchem | `ingredients` with CAS | `ingredients.iupac_name`, `ingredient_aliases` (synonyms) |
| 3   | obf-aliases | OBF dump | `ingredient_aliases` (label variants); `data/unmatched_tokens.csv` |
| 4   | pubmed | `ingredients` | `ingredient_sources` (abstracts) |
| 5   | editorial | `ingredient_sources` | `ingredient_content` (draft) |
| 6   | classify | `ingredients.function_tags` | `ingredients.skin_type_tag`, `ingredients.concern_tag` |
| 7   | products | OBF dump | `brands`, `products`, `product_ingredients` |

All stages are idempotent — re-run with `--force` to bypass the last-success guard.

### Why no CosIng

The EU Commission removed the CosIng bulk export in their 2023 site rebuild — only a search UI remains. We use the Open Beauty Facts ingredient taxonomy as the primary seed instead. It mirrors most CosIng entries, already carries CAS / EC / Wikidata IDs where known, and is published under an open license at `openbeautyfacts-server/taxonomies/ingredients.txt`. Sanity floor: ≥21,740 entries (the CosIng active-entry count).

## Decode (reference)

There is no API yet, but the matching cascade is a Postgres function so it's testable today:

```sql
select * from match_ingredient('aqua');
select * from match_ingredient('salycilic acid');     -- typo
select * from match_ingredient('Sodium Hyaluronate');
```

When an API lands, the decode endpoint will tokenize the input, call `match_ingredient` per token, and join `ingredient_content` where `status = 'published'`. Cache key: SHA256 of the normalized token list. TTL 24h.

## Notes on rating

`ingredients.rating` (`superhero`, `great`, `average`, `not_good`, `bad`) is never assigned by the pipeline. It's a human editorial judgment. Set it via the Supabase dashboard or a future curator UI.
