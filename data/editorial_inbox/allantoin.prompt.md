# Editorial prompt for: ALLANTOIN

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `allantoin.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: ALLANTOIN
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Allantoin.
Year: 1967
Abstract: 

PMID: unknown
Title: Purine catabolism by enterobacteria.
Year: 2023
Abstract: Purines are abundant among organic nitrogen sources and have high nitrogen content. Accordingly, microorganisms have evolved different pathways to catabolize purines and their metabolic products such as allantoin. Enterobacteria from the genera Escherichia, Klebsiella and Salmonella have three such pathways. First, the HPX pathway, found in the genus Klebsiella and very close relatives, catabolizes purines during aerobic growth, extracting all four nitrogen atoms in the process. This pathway includes several known or predicted enzymes not previously observed in other purine catabolic pathways. Second, the ALL pathway, found in strains from all three species, catabolizes allantoin during anaerobic growth in a branched pathway that also includes glyoxylate assimilation. This allantoin fermentation pathway originally was characterized in a gram-positive bacterium, and therefore is widespread. Third, the XDH pathway, found in strains from Escherichia and Klebsiella spp., at present is ill-defined but likely includes enzymes to catabolize purines during anaerobic growth. Critically, this pathway may include an enzyme system for anaerobic urate catabolism, a phenomenon not previously described. Documenting such a pathway would overturn the long-held assumption that urate catabolism requires oxygen. Overall, this broad capability for purine catabolism during either aerobic or anaerobic growth suggests that purines and their metabolites contribute to enterobacterial fitness in a variety of environments.

PMID: unknown
Title: [Allantoin].
Year: 2005
Abstract: 

PMID: unknown
Title: [Allantoin].
Year: 1999
Abstract: 

PMID: unknown
Title: Allantoin determination.
Year: 1977
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

