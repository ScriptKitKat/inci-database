# Dr. Jart Cicapair moisturizer verification loop

Tested July 14, 2026 against the local Supabase stack with the exact submitted
brand, product title, and ingredient label.

## Initial hypothesis

The exact product title and its published formula should verify automatically,
so the submission should move from `verifying` to `decision_ready` and then be
approved by the worker without curator review. Approval should create one
`Dr. Jart` brand, the submitted full product title, and 46 ordered ingredient
links without fragments from decimal commas or parenthetical synonyms.

## Loop 1 — tokenizer characterization

- Test case: the unmodified 46-ingredient label.
- Output snapshot: the pre-fix tokenizer returned 51 tokens. It split
  `1,2-HEXANEDIOL` into `1` and `2-HEXANEDIOL`; split the Shea and Cocoa
  parenthetical names; and separated both color names from their CI numbers.
- Comparison: failed before canonical writes and would have created junk rows.
- Change for the next loop: normalize backslashes to forward slashes, split only
  top-level list commas, preserve numeric commas, and retain parenthetical text
  inside its surrounding INCI name.

## Loop 2 — automatic verification and approval

- Test case: the same unmodified submission after delimiter and trusted-formula
  resolution changes.
- Database snapshot:

```text
parsed tokens: 46
status after verification: decision_ready
verification verdict: verified
submitted coverage: 1.0
online coverage: 1.0
status after apply worker: approved
brand: Dr. Jart (slug: dr-jart)
product: Cicapair™ Sensitive Skin Korean Face Moisturizer for Redness with Centella Asiatica
product_ingredients: 46, contiguous positions 1..46
null ingredient links: 0
unique linked ingredients: 46
new ingredient enrichment rows: 45
broken or junk ingredient names: 0
audit: intake by worker; verified by worker; approve by worker
```

- Notable preserved names: `Water`, `1,2-Hexanediol`,
  `Butyrospermum Parkii (Shea) Butter`, `Theobroma Cacao (Cocoa) Extract`,
  `Yellow 5 (Ci 19140)`, and `Blue 1 (Ci 42090)`.
- Comparison: matched the hypothesis with no `pending_human` transition.
- Change for the next loop: none. Focused regression tests now cover delimiter
  preservation, harmless shorter retailer titles, and deterministic creation
  from a fully matching trusted product formula.

All temporary submission, product, brand, ingredient, alias, enrichment, and
audit rows used for this replay were deleted after verification.
