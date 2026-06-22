# Editorial prompt for: RETINOL

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `retinol.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: RETINOL
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: SUPPLEMENT ARTICLE: Retinol: The Ideal Retinoid for Cosmetic Solutions.
Year: 2022
Abstract: Retinoids are a mainstay of dermatologic therapy. Although prescription retinoids are more potent than over the counter retinoids, when properly formulated cosmetic retinoids offer consumers an easily accessible, reasonably priced therapeutic option. Retinol has been shown to improve fine lines and wrinkles, hyperpigmentation, skin roughness, and the appearance of photoaged skin. The efficacy and tolerability of retinol makes it preferable to prescription retinoids as many patients are intolerant of these more potent forms. In this review, we will discuss the pharmacokinetics of retinol and the clinical studies confirming its efficacy, tolerability, and safety with long-term use. J Drugs Dermatol. 2022;21:7(Suppl):s4-10.

PMID: unknown
Title: [Retinol-binding protein (RBP)].
Year: 1983
Abstract: 

PMID: unknown
Title: Dietary retinol--a double-edged sword.
Year: 2002
Abstract: 

PMID: unknown
Title: Regulation of retinol-binding protein 4 and retinol metabolism in fatty liver disease.
Year: 2016
Abstract: 

PMID: unknown
Title: alpha-Retinol.
Year: 1978
Abstract: 

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

