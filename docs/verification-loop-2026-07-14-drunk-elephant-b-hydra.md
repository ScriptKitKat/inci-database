# Drunk Elephant B-Hydra verification loop

Tested July 14, 2026 against the local Supabase stack with the exact submitted
brand, product name, and 29-token label.

## Initial hypothesis

The 28 ingredients published for B-Hydra should resolve from a trusted product
formula. The additional `Monkeybutt fruit extract` token is absent from the
published formula and authoritative ingredient sources, so only that token
should require human review before the product can be approved.

## Loop 1 — queue and curator handoff

- Test case: exact user submission, including the extra final token.
- Database snapshot:

```text
submission id: 6b8c92a3-d063-4e48-b061-a4bd9d7174ed
status: pending_human
verification verdict: verified
submitted coverage: 0.9655 (28/29)
online coverage: 1.0 (28/28)
tokens: 29
new_ingredient: 28
pending_human: 1 (Monkeybutt fruit extract)
review trigger: llm_unknown
junk-like canonical names: 0
```

- Authenticated UI snapshot: the detail page rendered the exact product title,
  `Drunk Elephant`, all 29 tokens, and the single uncertain token without a
  server error. Its selector offers exactly `Matched`, `New ingredient`, and
  `Junk`; approval is disabled with `Resolve 1 tokens first` until the curator
  resolves the token.
- Comparison: matched the hypothesis. The submission never writes canonical
  brand, product, or ingredient rows before curator approval.
- Change for the next loop: none. The submission remains intentionally staged
  so the user can select `Junk`, confirm the drop, and approve as `Priscilla`.

After that manual approval, the expected canonical snapshot is one
`Drunk Elephant` brand, the exact submitted B-Hydra product title, and 28
ordered non-null `product_ingredients`; no Monkeybutt ingredient row should
exist. Cleanup should occur only after that manual result has been inspected.

## Loop 2 — match existing ingredient

- Test case: use the curator's `Matched` control to select remote catalog rows
  for `Water`, `Glycerin`, and `Coconut Alkanes`.
- Initial result: autocomplete returned the correct remote rows, but Confirm
  match rolled back because those UUIDs were not present in the local review
  database's `ingredients` table.
- Change for the next attempt: validate the selected UUID against the remote
  catalog, synchronize that canonical row into the review database through the
  restricted `sync_remote_catalog_ingredient` function, then resolve the token
  with the synchronized ID. Update the optimistic row with the canonical name.
- Database snapshot after the fix:

```text
Water/Aqua/Eau   matched  9a75d2af-09bb-4270-90c5-3c9259085846  Water
Coconut Alkanes matched  171a36bc-ca3b-4ea1-95bc-f0c20504fe55  COCONUT ALKANES
Glycerin         matched  01c3c5a5-0c55-4b55-a241-ca833039563f  GLYCERIN
Monkeybutt fruit extract remains junk
submission status remains pending_human
```

- Comparison: the confirmed tokens now use `matched`, retain the existing
  remote canonical UUIDs, and expose their canonical names in the review-page
  payload. Approval will therefore write those IDs directly into
  `product_ingredients` rather than creating new ingredient rows.

## Loop 3 — automatic remote exact matching

- Test case: run deterministic matching for `glycerin` and `niacinamide` while
  the canonical catalog is remote and the review database starts without the
  latter ingredient.
- Initial result: intake queried only the review database. Consequently,
  canonical ingredients already present remotely could proceed as
  `new_ingredient` when the local development catalog was sparse.
- Change for the next attempt: after checking the review database, query the
  remote catalog's deterministic matcher. Accept only `canonical_exact` and
  `alias_exact`, synchronize the trusted canonical row through
  `sync_remote_catalog_ingredient`, and stage the token as `matched`. Retain
  local fuzzy results only as hypotheses; never auto-link a remote fuzzy hit.
- Database snapshot:

```text
glycerin    canonical_exact  1.0  01c3c5a5-0c55-4b55-a241-ca833039563f
niacinamide canonical_exact  1.0  17ebfbcf-894c-4b22-a8bf-a07eddbae514

Current B-Hydra reconciliation:
16 previously-new tokens changed to matched remote ingredients
8 tokens remain new ingredients because the remote matcher has no exact hit
Monkeybutt fruit extract remains junk
```

- Comparison: exact existing catalog ingredients can no longer be created as
  new ingredients. The requested Glycerin UUID is preserved. Botanical names
  with only fuzzy candidates remain unlinked for safety.

## Loop 4 — approved canonical-table verification

- Test case: curator approves submission
  `6b8c92a3-d063-4e48-b061-a4bd9d7174ed` after resolving Monkeybutt as junk.
- Initial result: the product, brand, and 28 ordered links were written
  correctly. A semantic comparison found two avoidable new rows whose submitted
  spellings differed from remote canonical names only by parenthetical common
  names: Pineapple and Lentil.
- Change for the next attempt: when the raw spelling has a parenthetical
  alphabetic common name, remove that parenthetical phrase and require an exact
  local or remote match. Correct the two approved links, preserve the submitted
  spellings as aliases, and delete the unreferenced duplicate rows.
- Final database snapshot:

```text
product: 06c30435-6ec6-44c0-b71d-b0a181273747
brand: Drunk Elephant
name: B-Hydra™ Intensive Hydration Serum with Hyaluronic Acid
product_ingredients: 28, positions 1 through 28, null links 0
submission tokens: matched 28, junk 1
Glycerin: 01c3c5a5-0c55-4b55-a241-ca833039563f
Ananas Sativus Fruit Extract: 2ed67a3e-7ef0-4126-b05f-3ef756ca9444
Lens Esculenta Fruit Extract: 9358aab3-8e5e-4663-8e70-8854adf1156f
Monkeybutt ingredient rows: 0
superseded duplicate rows: 0
```

- Comparison: the approved product now matches the expected canonical layout.
  Existing remote IDs are reused, all ordered product links are non-null, and
  the junk token did not enter the ingredient catalog.
