---
noteId: "94f83f606e6711f1b57f8b273f55ec93"
tags: []

---

# Editorial prompt for: Sulfur

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `sulfur.json` in this same folder.
Run `inci-pipeline import-editorial` after you've collected responses.

---

You are an editorial writer for a skincare ingredient database. Use your existing knowledge of dermatology and cosmetic chemistry to write a profile for a general audience. No source abstracts are provided — if you're uncertain about a specific claim, hedge it ("limited evidence", "anecdotal", "needs confirmation").

Ingredient: Sulfur

Return a JSON object with EXACTLY these keys. Do not wrap in code fences. Do not add extra keys.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), suitable for a decode result. Lead with the single most useful fact.
- `summary_long`: 3–6 paragraphs of Markdown covering mechanism, evidence quality, typical concentrations, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 short bullet strings (<80 chars each).

Constraints:
- Never invent claims; hedge when unsure.
- Never assign an overall rating — reserved for human curators.
- Keep tone informative, not promotional.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.


Return JSON only.
