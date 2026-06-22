# Editorial prompt for: BISABOLOL

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `bisabolol.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: BISABOLOL
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Bisabolol.
Year: 2017
Abstract: 

PMID: unknown
Title: Bisabolol.
Year: 2010
Abstract: Bisabolol is an active plant extract isolated from German chamomile and thought to have antiinflammatory and skin-soothing properties. It is a common additive in many products, including moisturizing creams and ointments, lotions, cleansers, sunscreens, antiperspirants, and makeup products. Contact dermatitis from bisabolol has been reported in Europe and is purported to occur in the United States. Patch testing with bisabolol-containing products or bisabolol may be useful in the work-up of patients with presumptive allergic contact dermatitis or potentially worsening atopic dermatitis. Patients sensitized to bisabolol should be counseled to avoid any bisabolol-containing products.

PMID: unknown
Title: A review of the bioactivity and potential health benefits of chamomile tea (Matricaria recutita L.).
Year: 2006
Abstract: Chamomile (Matricaria recutita L., Chamomilla recutita L., Matricaria chamomilla) is one of the most popular single ingredient herbal teas, or tisanes. Chamomile tea, brewed from dried flower heads, has been used traditionally for medicinal purposes. Evidence-based information regarding the bioactivity of this herb is presented. The main constituents of the flowers include several phenolic compounds, primarily the flavonoids apigenin, quercetin, patuletin, luteolin and their glucosides. The principal components of the essential oil extracted from the flowers are the terpenoids alpha-bisabolol and its oxides and azulenes, including chamazulene. Chamomile has moderate antioxidant and antimicrobial activities, and significant antiplatelet activity in vitro. Animal model studies indicate potent antiinflammatory action, some antimutagenic and cholesterol-lowering activities, as well as antispasmotic and anxiolytic effects. However, human studies are limited, and clinical trials examining the purported sedative properties of chamomile tea are absent. Adverse reactions to chamomile, consumed as a tisane or applied topically, have been reported among those with allergies to other plants in the daisy family, i.e. Asteraceae or Compositae.

PMID: unknown
Title: Biotransformation of (-)-α-Bisabolol by 
Year: 2022
Abstract: (-)-α-Bisabolol, a bioactive monocyclic sesquiterpene alcohol, has been used in pharmaceutical and cosmetic products with anti-inflammatory, antibacterial and skin-caring properties. However, the poor water solubility of (-)-α-bisabolol limits its pharmaceutical applications. It has been recognized that microbial transformation is a very useful approach to generate more polar metabolites. Fifteen microorganisms were screened for their ability to metabolize (-)-α-bisabolol in order to obtain its more polar derivatives, and the filamentous fungus

PMID: unknown
Title: RIFM fragrance ingredient safety assessment, α-bisabolol, CAS registry number 515-69-5.
Year: 2020
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

