# User-Submitted Product Verification Pipeline — Design

Date: 2026-07-09 (approved 2026-07-10)

## Context

The repo has a Supabase schema, a Python seeding pipeline (`pipeline/`), and a
product-ingredient cleanup ETL (`ETL Ingredients from Products/`). There is no way for an
end user to submit a product. The goal: users submit a product (brand, name, pasted
ingredient list); the system verifies the product is real, verifies/normalizes every
ingredient against authoritative sources, escalates ambiguous cases to a human reviewer,
and only then writes to the public catalog (`brands`, `products`, `product_ingredients`,
`ingredients`).

**Critical lesson from the existing ETL:** it produced misspelled and non-existent
ingredients. Root cause: canonical names could originate from LLM judgment over label
tokens. The new pipeline is **prevention, not cure** — nothing enters canonical tables
until verified, and a canonical ingredient spelling can ONLY come from an exact string in
an authoritative source, never from the LLM.

The old ETL folder is ignored (not deleted, not depended on), but good parts are copied:
evidence lookups, Anthropic batch helpers, queue/claim SQL patterns.

CosIng constraint: the EU Commission removed the CosIng bulk export in the 2023 site
rebuild. The OBF ingredient taxonomy remains the primary nomenclature source; the CosIng
search UI is a best-effort per-token evidence source only.

## Decisions

| Question | Decision |
|---|---|
| Volume/latency | Low volume, async. Submitter gets "pending verification"; processing completes in ~30–60 min |
| Staging | Separate `product_submissions` tables. Canonical rows created only at approval, in one transaction |
| List mismatch vs online | Auto-accept if >=0.90 token overlap; escalate divergent with side-by-side diff |
| New ingredients | Auto-create only on exact authoritative-source hit + LLM concurrence; else human review |
| Review UI | Minimal Next.js app included in this project |
| Product descriptions | LLM (Haiku, batched) at approval time, 1–2 sentences |
| Ingredient descriptions | Deferred — NOT wired into this pipeline; designed separately later |
| Worker runtime | GitHub Actions cron (~every 30 min) running the Python worker |
| Code home | New standalone folder `submission-pipeline/` |

## Architecture

```
User (app / review-UI form / CLI)
  -> INSERT product_submissions (status=received)          [RLS: authenticated insert]

GitHub Actions cron (*/30) -> `submission-pipeline run`:
  1. poll_batches   — retrieve finished Anthropic batches, write verdicts/resolutions
  2. intake         — claim received rows: tokenize_label -> fingerprint dupe-check
                      -> match_ingredient per token -> deterministic evidence lookups
  3. submit_batch   — one Anthropic Batch: product web-search verification
                      + per-unresolved-token judgment
  4. apply          — auto-approve decision_ready rows via apply_product_submission()
  5. describe       — batch Haiku short_descriptions for new products missing one
  6. purge          — delete rejected/duplicate rows >30 days old

Human reviewer (Next.js review-ui) -> resolve tokens / approve / reject via RPCs
```

All state lives in Postgres. Claiming uses `FOR UPDATE SKIP LOCKED` + `locked_at` +
`attempt_count` (same pattern as `claim_ingredient_name_curation_queue`). Every step is
idempotent; the workflow has a `concurrency` group so runs never overlap.

## Schema (migration `supabase/migrations/20260710000100_product_submissions.sql`)

- `product_submissions` — one row per submitted product: submitter, brand/product names,
  `raw_ingredient_text`, `ingredient_fingerprint`, status
  (`received | triaging | verifying | decision_ready | pending_human | approved | rejected | duplicate | failed`),
  `verification` JSONB (`{found, source_name, source_url, overlap, verdict, online_tokens?}` —
  `online_tokens` stored only when divergent), `anthropic_batch_id`, `product_id` (set on
  approve; on duplicate points at the existing product), worker fields (`locked_at`,
  `attempt_count`, `last_error`), review fields, timestamps.
- `submission_tokens` — one row per parsed ingredient token: position, raw/normalized
  token, match result (`matched_ingredient_id`, `match_type`, `match_confidence`),
  `resolution` (`unresolved | matched | new_ingredient | junk | unmatched_keep | pending_human`;
  `unmatched_keep` is human-only), `canonical_name` (exact string from an authoritative
  source), compact `evidence` JSONB array (no raw payloads), `resolution_source`
  (`exact_match | deterministic | llm | human`). UNIQUE (submission_id, position).
- `curators` — user_id allowlist for review access.
- `submission_audit` — action log (submission_id, action, actor, payload).
- `ALTER TYPE source_type ADD VALUE 'user_submission'` for alias provenance.

RPCs (SECURITY DEFINER; mutations require service role or curators membership):

- `claim_product_submissions(p_status, p_limit)` — SKIP LOCKED claim.
- `fail_product_submission(p_id, p_error, p_max_attempts = 3)` — retry/fail.
- `resolve_submission_token(p_token_id, p_resolution, p_ingredient_id, p_canonical_name)` —
  human token action; validates curator; writes audit.
- `apply_product_submission(p_id, p_actor)` — the ONLY writer to canonical tables. One
  transaction: guard (all tokens resolved; fingerprint race re-check); upsert brand;
  insert `new_ingredient` tokens as ingredients (inci_name = canonical_name, existing slug
  recipe, raw token as alias when different; no editorial enqueue); add typo/synonym
  aliases for LLM/human-confirmed variants; insert product (slug recipe, fingerprint,
  short_description NULL); insert product_ingredients (junk dropped, unmatched_keep kept
  with NULL ingredient_id); mark approved; null heavy JSONB; audit.
- `reject_product_submission(p_id, p_reason, p_actor)`.
- `purge_stale_submissions(p_days = 30)`.

RLS: submitters INSERT/SELECT own rows; curators SELECT all; no anonymous read; all
writes beyond INSERT go through RPCs.

## Decision policy (anti-garbage rules)

| Signal | Outcome | Path |
|---|---|---|
| `match_ingredient` exact/alias (>=0.98) | `matched` | deterministic, intake |
| Exact normalized hit in OBF taxonomy / PubChem / CosIng search / INCIDecoder mapping to an existing ingredient | `matched` | deterministic, intake |
| Exact authoritative hit, no existing ingredient, + LLM concurs it is a cosmetic ingredient | `new_ingredient`, `canonical_name` = source's exact string | LLM batch |
| PubChem-only evidence (no INCI-native source hit) | corroboration only — never donates a spelling, so no `new_ingredient` hypothesis | `pending_human` unless another rail resolves it |
| Fuzzy match >=0.85 + LLM confirms same substance | `matched` + typo alias at apply | LLM batch |
| LLM >=0.90 confident token is label noise | `junk` | LLM batch |
| Everything else — incl. LLM believing an ingredient is real WITHOUT an authoritative exact hit | `pending_human` | human |

Product-level: agent (Claude + web_search, batched) locates the product; token overlap vs
submitted list. `found && overlap >= 0.90` -> verified. Not found or divergent ->
`pending_human` (online list retained for the diff view). Auto-approve requires verified
product AND zero pending_human tokens. A config flag falls back to synchronous Messages
calls if web_search-in-batches misbehaves.

Hardening vs the failed ETL: the LLM never supplies a canonical spelling — it only picks
between hypotheses anchored to authoritative strings or flags junk; no fuzzy auto-creates;
all canonical writes go through one audited transactional RPC.

Spelling-source hierarchy: only INCI-native sources may donate `canonical_name`
(`SPELLING_SOURCES` = CosIng > INCIDecoder > OBF, confidences 0.97 / 0.92 / 0.90).
PubChem (0.85) is a chemistry database whose renderings are not INCI names: it returns
evidence only when a synonym exactly matches the normalized token (no first-synonym
fallback) and its evidence corroborates existence but never becomes a hypothesis
spelling.

## Answers to the open design questions

1. **Aliasing/matching**: reuse the `match_ingredient` cascade + `ingredient_aliases`
   (provenance `user_submission`). Every confirmed variant becomes an alias at apply time,
   so repeat submissions hit `alias_exact` and skip the LLM entirely.
2. **Ingredient descriptions**: deferred; new ingredients get no writeup and no automatic
   curation-queue entry. Separate future pipeline.
3. **Product descriptions**: `describe` stage batches Haiku 4.5 calls (brand + name +
   matched ingredients' function tags -> 1–2 sentences). `search_vector` updates via the
   existing trigger.

## Components

`submission-pipeline/` (standalone, package `submission_pipeline`, no cross-folder imports):

- Copied/adapted: `normalize.py` (from `pipeline/`), `evidence.py` (from
  `ETL .../sources/ingredient_verification.py`, plus best-effort CosIng search-UI and
  INCIDecoder lookups), `llm/batch.py` (from `ETL .../curation/llm_batch.py`; parsed
  decisions only, payloads never persisted), `db.py`, `config.py`, `matching.py` (thin
  `match_ingredient` RPC wrapper).
- New: `stages/intake.py`, `stages/verify.py`, `stages/apply.py`, `stages/purge.py`,
  `llm/prompts/{verify_product,verify_token,product_description}.md`, `cli.py`
  (`run [--once]`, `submit`), `tests/`.
- Models: judgments Sonnet 4.6; descriptions Haiku 4.5.

`review-ui/` (Next.js App Router + TypeScript + Supabase JS + Supabase Auth email OTP;
curators only; mutations via RPCs only):

- `/` — queue of pending_human submissions (brand, product, age, unresolved count).
- `/submissions/[id]` — evidence header; submitted-vs-online diff when divergent; token
  table with actions (accept suggestion / search-and-pick via `match_ingredient` /
  create new with canonical name pre-filled from evidence / junk / keep-unmatched);
  Approve / Reject.
- Small "new submission" form.

`.github/workflows/submissions.yml` — cron `*/30 * * * *` + workflow_dispatch,
`concurrency: submissions`, installs and runs `submission-pipeline run`.

## Storage minimalism (limited Supabase plan)

- Compact evidence JSONB on token rows; no separate evidence/edges tables.
- Online ingredient list stored only for divergent products.
- Batch bodies never persisted; only batch id + parsed results.
- Heavy JSONB nulled at apply; `purge_stale_submissions(30)` every cron tick.
- No images/binary data.

## Verification

1. `supabase db reset && supabase db push` applies cleanly.
2. pytest (mock Anthropic, local Supabase) — six scenarios: clean full match; typo token;
   real-but-new ingredient (mock CosIng exact hit -> auto-create with source spelling;
   a PubChem-only hit must NOT auto-create);
   junk token; divergent product list -> pending_human; duplicate fingerprint.
3. CLI E2E: `submission-pipeline submit` with a real label -> `run --once` twice ->
   assert product/product_ingredients/aliases/audit rows.
4. Review UI: log in as seeded curator, resolve a pending_human fixture, approve, confirm
   product via SQL; Playwright smoke of the same path.
5. Quality guard: a misspelled fake ingredient ("Hyaluronic Asid Extreme") must land
   pending_human, never auto-created.

## Out of scope

- Consumer-facing app beyond the curator tool's submission form.
- Fixing/removing the old `ETL Ingredients from Products/` folder.
- Backfilling existing catalog products through the new verifier.
- Editorial/rating pipeline changes; ingredient descriptions for new ingredients.
