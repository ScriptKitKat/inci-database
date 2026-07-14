# La Roche-Posay tinted sunscreen verification loop

Tested July 14, 2026 against the local Supabase stack. The submitted brand was
`La Roche-Posay`, the submitted product name was `Sun Screen`, and the label was
the active/inactive ingredient text supplied by the user.

## Initial hypothesis

The submission should enter the worker queue and stop in human review because
the generic submitted name needs confirmation against the manufacturer's full
product title. After the curator confirms the resolved name and the one missing
catalog ingredient, approval should create one product with 40 ordered,
non-null ingredient links and no heading, concentration, or bullet-list junk.

## Loop 1 — tokenizer characterization

- Test case: the unmodified drug-facts label, including Markdown headings,
  `(Tinted Shade)`, `11%`, and bullet separators.
- Database/output snapshot: the pre-fix tokenizer returned 54 tokens, including
  `**ACTIVE INGREDIENTS`, `Tinted Shade`, `11`, and
  `**INACTIVE INGREDIENTS`; it also split multi-word INCI names.
- Comparison: failed the hypothesis before any canonical write. Sending this
  output to approval would have polluted `ingredients`.
- Change for the next loop: strip active/inactive section headings and trailing
  percentages, treat bullets as authoritative delimiters, and reserve the
  all-caps whitespace fallback for labels with no explicit separators.

## Loop 2 — queue and human-review result

- Test case: the same unmodified submission after the tokenizer and guarded
  product-name resolution changes.
- UI snapshot: the authenticated server-rendered review page contained the
  resolved title, the original `Sun Screen` value, the product-name confirmation
  warning, and the unresolved `DIETHYLHEXYL SYRINGYLIDENEMALONATE` row.
- Database snapshot:

```text
status: pending_human
brand_name: La Roche-Posay
product_name: Anthelios Mineral Tinted Sunscreen for Face with SPF
verification.verdict: name_resolved
verification.submitted_product_name: Sun Screen
submitted_coverage: 1.0
online_coverage: 1.0
tokens: 40 (39 matched, 1 unresolved)
junk-like tokens: 0
review trigger: product_name_resolved
```

- Comparison: matched the hypothesis. The canonical title came from the trusted
  manufacturer page, but the change was not auto-approved.
- Change for the next loop: no prompt change. The curator marked the one absent
  INCI name as `new_ingredient` and approved as `Priscilla`.

## Loop 3 — curator approval and canonical writes

- Test case: approve the Loop 2 review after resolving the missing ingredient.
- Database snapshot:

```text
submission status: approved
brand: La Roche-Posay (slug: la-roche-posay)
product: Anthelios Mineral Tinted Sunscreen for Face with SPF
product_ingredients: 40
positions: contiguous 1..40
null ingredient links: 0
junk ingredient rows: 0
new ingredient rows: 1 (DIETHYLHEXYL SYRINGYLIDENEMALONATE)
new ingredient enrichment status: unfilled
curator audit: resolve_token by Priscilla; approve by Priscilla
```

- Comparison: matched the hypothesis. `product_ingredients` references the
  canonical product and ingredient rows in label order, and no headings,
  percentages, or combined bullet list became ingredients.
- Change for the next loop: none; this pathway is covered by focused tokenizer,
  verification, migration-contract, and curator UI tests.

All temporary submission, product, brand, ingredient, and enrichment rows used
for this replay were deleted after verification.
