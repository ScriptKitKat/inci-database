# Glow Recipe Dew Drops remote verification loop

Tested July 14, 2026 against hosted Supabase project
`xwdmtipxfgcxfemnizie` with the exact 23-token submission.

## Initial hypothesis

The known Glow Recipe formula should achieve full trusted-source coverage,
reuse exact remote ingredients, and reach automatic approval without curator
review. Canonical ingredients absent from the hosted catalog should be created
once with enrichment shells, while multilingual names should resolve as
aliases.

## Loop 1 — remote intake and product-name comparison

- Test case: exact submitted brand, title, and ingredient label.
- Snapshot: submission `0eccfd66-1c63-438e-82d5-20e927a9399a`; 19 exact
  matches, four unresolved tokens, zero intake escalations.
- Comparison: ingredient intake matched expectations, but verification emitted
  `name_resolved` because the published title redundantly prefixed `Glow Recipe`
  to the separately stored brand.
- Change for the next attempt: ignore one normalized leading brand prefix when
  comparing submitted and published product titles.

## Loop 2 — official-domain trust

- Test case: repeat product verification after restoring the submitted title.
- Snapshot: exact official Glow Recipe URL, submitted coverage `1.0`, online
  coverage `1.0`, but verdict `untrusted_source`.
- Comparison: formula and product were correct; `glowrecipe.com` was absent from
  the brand-domain allowlist.
- Change for the next attempt: register `glowrecipe.com` for `GLOW RECIPE` and
  deterministically re-evaluate the stored official evidence.

## Loop 3 — remote approval and semantic link audit

- Test case: automatically apply the resulting `decision_ready` submission.
- Initial snapshot: hosted product and all 23 links were created, but position 7
  linked `1,2-Hexanediol` to generic `HEXANEDIOL` because source evidence had
  dropped its numeric qualifier.
- Comparison: structurally correct but semantically inaccurate at one position.
- Change for the next attempt: deterministic evidence matches must preserve all
  numeric components. Create canonical `1,2-Hexanediol`, repair position 7, and
  remove the incorrect generic-Hexanediol alias.

## Final hosted database snapshot

```text
submission: 0eccfd66-1c63-438e-82d5-20e927a9399a (approved)
product: 09fd0a15-b07c-47bc-983a-f51a1ec57d1e
brand: Glow Recipe (exactly one row)
name: Watermelon Glow Niacinamide Dew Drops (exactly one row)
product_ingredients: 23, positions 1–23, null links 0
submission tokens: matched 23
bad/junk product ingredient names: 0
incorrect 1,2-Hexanediol aliases on HEXANEDIOL: 0

Existing examples:
GLYCERIN   01c3c5a5-0c55-4b55-a241-ca833039563f
NIACINAMIDE 17ebfbcf-894c-4b22-a8bf-a07eddbae514

New canonical rows (all have information, writeup, and enrichment queue rows):
1,2-Hexanediol                    69ba27dd-7478-4e84-bfc5-949b099bbce7
2,3-Butanediol                    03e9d277-b6cc-478e-9793-dee3b4862c3c
Citrullus Lanatus Fruit Extract  33b88bdc-b360-4057-b86c-6df133aaa135
Eclipta Prostrata Extract         d8328cff-665a-40e5-a342-374410cd1d79
Moringa Oleifera Seed Oil         dfbb80bc-1f9c-47fc-b35b-a3bfe0413320
```

The final hosted canonical state matches the expected product, brand, ordered
formula, reuse behavior, and new-ingredient enrichment behavior.
