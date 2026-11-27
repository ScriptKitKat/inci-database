# inci-database

Supabase-backed skincare ingredient and product catalog, with a submission worker and a curator app for manual review.

## Layout

```
inci-database/
  supabase/migrations/             # database schema and RPCs
  submission-pipeline/             # product submission verification worker
  curator-ui/                     # manual submission review app
  ETL Ingredients from Products/  # standalone cleanup tooling
  .github/workflows/              # submission worker and PR checks
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

## Decode (reference)

The ingredient matching cascade is available as a Postgres function:

```sql
select * from match_ingredient('aqua');
select * from match_ingredient('salycilic acid');     -- typo
select * from match_ingredient('Sodium Hyaluronate');
```

## Notes on rating

`ingredient_information.rating` (`ew_ew`, `okie`, `yippe`, `wowza`) is a human editorial judgment. Set it via the Supabase dashboard.
