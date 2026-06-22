# Editorial prompt for: CITRIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `citric-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: CITRIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Citric acid cycle intermediates in cardioprotection.
Year: 2014
Abstract: Over the last decade, there has been a concerted clinical effort to deliver on the laboratory promise that a variety of maneuvers can profoundly increase cardiac tolerance to ischemia and/or reduce additional damage consequent upon reperfusion. Here we will review the proximity of the metabolic approach to clinical practice. Specifically, we will focus on how the citric acid cycle is involved in cardioprotection. Inspired by cross-fertilization between fundamental cancer biology and cardiovascular medicine, a set of metabolic observations have identified novel metabolic pathways, easily manipulable in man, which can harness metabolism to robustly combat ischemia-reperfusion injury.

PMID: unknown
Title: Citric Acid: Properties, Microbial Production, and Applications in Industries.
Year: 2023
Abstract: Citric acid finds broad applications in various industrial sectors, such as the pharmaceutical, food, chemical, and cosmetic industries. The bioproduction of citric acid uses various microorganisms, but the most commonly employed ones are filamentous fungi such as

PMID: unknown
Title: Citric acid production.
Year: 2007
Abstract: Citric acid is a commodity chemical produced and consumed throughout The World. It is used mainly in the food and beverage industry, primarily as an acidulant. Although it is one of the oldest industrial fermentations, its World production is still in rapid increasing. Global production of citric acid in 2007 was over 1.6 million tones. Biochemistry of citric acid fermentation, various microbial strains, as well as various substrates, technological processes and product recovery are presented. World production and economics aspects of this strategically product of bulk biotechnology are discussed.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

