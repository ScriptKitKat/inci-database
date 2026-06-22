You normalize messy chemical synonym strings into clean ingredient aliases.

Input synonyms (raw, may contain noise):
{synonyms}

Return a JSON array of strings. Filter out:
- Catalog numbers (e.g., "CAS 12345-67-8", "EC 200-712-3").
- Pure stoichiometric strings (e.g., "C9H8O3").
- Marketing names with embedded percentages.
- Duplicates after case-folding.

Keep:
- Plain-language common names.
- IUPAC-derived names.
- Pharmacopoeia names.
- Trade names that appear on product labels.

Return JSON array only. No fences. Maximum 25 strings.
