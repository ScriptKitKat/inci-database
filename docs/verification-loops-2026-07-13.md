# Parts 2–3 verification loops — 2026-07-13

The local Supabase stack was used for every database snapshot. Browser-rendered
HTML was checked through authenticated HTTP requests because the in-app browser
runtime failed during initialization; database snapshots are the requested
alternative evidence. All rows listed here use the `Codex Loop Labs` fixture
namespace and are deleted at the end of the run.

## Loop 1 — deterministic intake, product not found, curator approval

**Test case.** Brand `Codex Loop Labs`, product `Two Ingredient Test Serum`,
ingredients `Water, Glycerin`.

**Initial hypothesis (two sentences).** Both exact catalog spellings will resolve
deterministically at intake. The nonexistent product will receive `not_found`,
enter `pending_human`, and curator approval will create one product with two
canonical ingredient links.

**Database snapshot before review.**

```text
status: pending_human
verification.verdict: not_found
1 | Water    | matched | exact_match
2 | Glycerin | matched | exact_match
```

Authenticated queue/detail rendering returned HTTP 200 and contained the product
name, trigger, both tokens, and Approve/Reject controls.

**Database snapshot after review.**

```text
approved | Two Ingredient Test Serum | Codex Loop Labs
1 | Water
2 | Glycerin
audit: intake(worker) -> verified(worker) -> approve(Priscilla)
```

**Comparison.** Exact match. The first authenticated REST query exposed missing
explicit `service_role` table grants under Supabase's newer non-auto-exposure
default.

**Change for the next loop.** Added a narrowly scoped grant migration, then
changed the input to a fuzzy typo so the next loop exercised the `matched`
curator action and alias emission.

## Loop 2 — curator matches a typo

**Test case.** Product `Typo Match Serum`, token `Glycerrin`, fuzzy candidate
Glycerin at 0.88.

**Hypothesis.** Selecting `matched` will link the existing Glycerin row and
approval will emit one validated typo alias. It will not create another
Glycerin ingredient.

**Database snapshot.**

```text
approved | Typo Match Serum | Glycerin | Glycerrin | typo | user_submission
count(ingredients where normalized_name='glycerin'): 1
```

**Comparison.** Exact match; no inaccurate or missing write was found.

**Change for the next loop.** Changed the token to a source-backed canonical
name absent from the catalog to exercise `new_ingredient`.

## Loop 3 — curator creates a new ingredient

**Test case.** Product `New Ingredient Serum`, token and CosIng fixture canonical
`Codexium Extract`.

**Hypothesis.** `new_ingredient` will create exactly one canonical ingredient,
link it to the product, and create the required enrichment and editorial shells.

**Database snapshot.**

```text
approved | New Ingredient Serum | Codexium Extract | enrichment=unfilled | editorial=draft
```

**Comparison.** Exact match; canonical spelling came from curator input and not
LLM output.

**Change for the next loop.** Changed the first token to obvious label noise to
exercise the high-position junk guard, all-junk apply guard, and rejection.

## Loop 4 — high-position junk and rejection

**Test case.** Product `All Noise Fixture`, position-1 token
`Directions: apply nightly`.

**Hypothesis.** The UI presents the second high-position confirmation, resolving
the token as junk makes apply return `pending_human`, and a reasoned rejection
creates no product.

**Database snapshot.**

```text
status: rejected
reject_reason: Ingredient list is nonsense
product_id: null
audit: pending_human(junk_at_top_positions) -> resolve_token(Priscilla)
       -> pending_human(all_tokens_junk) -> reject(Priscilla)
```

**Comparison.** Exact match. Review found that the older reject RPC accepted
short reasons and non-review statuses when called outside the UI.

**Change for the next loop.** Tightened the RPC to a 10-character minimum and
`pending_human`/`decision_ready` statuses, then changed the case to an exact
formula with a different product name.

## Loop 5 — similar formula, different product name

**Test case.** Existing `Two Ingredient Test Serum`; submitted
`Twin Formula Serum`, same `Water, Glycerin` formula.

**Hypothesis.** Intake will produce `similar_product` at 1.0 rather than
`duplicate`; the detail page will identify the existing product and require the
separate-product confirmation; approval can create a distinct product.

**Rendered/database snapshot.**

```text
pending_human | verdict=similar_product | similarity=1.0
rendered: Twin Formula Serum
rendered: Two Ingredient Test Serum
rendered: The formulas overlap by at least 95%, but the product names differ.
after approval: approved | Twin Formula Serum | Codex Loop Labs
```

**Comparison.** Exact match. The detail warning initially used the 95%-overlap
copy for the separate same-name/different-formula case too.

**Change for the next loop.** Split the warning copy by verdict, then restored
the exact original identity to verify automatic duplicate handling.

## Loop 6 — exact same-product duplicate

**Test case.** Brand, product, and formula all equal the approved
`Two Ingredient Test Serum`.

**Hypothesis.** Intake will stop at `duplicate`, link the existing product, and
create neither staging token rows nor a verification batch.

**Database snapshot.**

```text
duplicate | existing Two Ingredient Test Serum product id | token_rows=0
intake counters: duplicates=1, queued=0, human_review=0
```

**Comparison.** Exact match. No further implementation change was needed; this
case is retained in focused intake tests.

## Automated pathway coverage

The repeatable suites cover the combinations that should not depend on mutable
external web results: bounded batch splitting, oversized submissions, duplicate
custom IDs, send/attach failure release, retry-to-sync fallback, stale batch
rejection, malformed/missing product and token results, trusted/lookalike URL
hosts, one-to-one bidirectional overlap, source disagreement, all LLM verdict and
confidence rails, queue trigger labels, all three approvable token states, and
empty/unresolved approval guards.
