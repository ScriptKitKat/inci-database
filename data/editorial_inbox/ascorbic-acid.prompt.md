# Editorial prompt for: ASCORBIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `ascorbic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: ASCORBIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Current studies on the enzymatic preparation 2-O-α-d-glucopyranosyl-l-ascorbic acid with cyclodextrin glycosyltransferase.
Year: 2019
Abstract: 2-O-α-d-glucopyranosyl-l-ascorbic acid (AA-2G) is one of the most important l-ascorbic acid derivatives because of its resistance to reduction and oxidation and its easy degradation by α-glucosidase to release l-ascorbic acid and glucose. Thus, AA-2G has commercial uses in food, medicines and cosmetics. This article presents a review of recent studies on the enzymatic production of AA-2G using cyclodextrin glycosyltransferase. Reaction mechanisms with different donor substrates are discussed. Protein engineering, physical and biological studies of cyclodextrin glycosyltransferase are introduced from the viewpoint of effective AA-2G production. Future prospects for the production of AA-2G using cyclodextrin glycosyltransferase are reviewed.

PMID: unknown
Title: Ascorbic acid and ferritin catabolism.
Year: 1989
Abstract: Ascorbic acid blocks the degradation of cytoplasmic ferritin by reducing lysosomal autophagy of the protein.

PMID: unknown
Title: Oxidation of Ascorbic Acid to Dehydroascorbic Acid.
Year: 1947
Abstract: 

PMID: unknown
Title: Editorial: Ascorbate metabolism in plants.
Year: 2023
Abstract: 

PMID: unknown
Title: Ascorbic-acid metabolism.
Year: 1947
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

