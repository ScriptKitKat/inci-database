# Editorial prompt for: DISODIUM EDTA

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `disodium-edta.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: DISODIUM EDTA
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: EDTA and Salts.
Year: 2023
Abstract: The Expert Panel for Cosmetic Ingredient Safety reviewed newly available studies since their original assessment in 1998, along with updated information regarding product types and concentrations of use and confirmed that EDTA and certain salts are safe as cosmetic ingredients in the practices of use and concentration as described in this report.

PMID: unknown
Title: Final report on the safety assessment of EDTA, calcium disodium EDTA, diammonium EDTA, dipotassium EDTA, disodium EDTA, TEA-EDTA, tetrasodium EDTA, tripotassium EDTA, trisodium EDTA, HEDTA, and trisodium HEDTA.
Year: 2002
Abstract: EDTA (ethylenediamine tetraacetic acid) and its salts are substituted diamines. HEDTA (hydroxyethyl ethylenediamine triacetic acid) and its trisodium salt are substituted amines. These ingredients function as chelating agents in cosmetic formulations. The typical concentration of use of EDTA is less than 2%, with the other salts in current use at even lower concentrations. The lowest dose reported to cause a toxic effect in animals was 750 mg/kg/day. These chelating agents are cytotoxic and weakly genotoxic, but not carcinogenic. Oral exposures to EDTA produced adverse reproductive and developmental effects in animals. Clinical tests reported no absorption of an EDTA salt through the skin. These ingredients are likely, however, to affect the passage of other chemicals into the skin because they will chelate calcium. Exposure to EDTA in most cosmetic formulations, therefore, would produce systemic exposure levels well below those seen to be toxic in oral dosing studies. Exposure to EDTA in cosmetic formulations that may be inhaled, however, was a concern. An exposure assessment done using conservative assumptions predicted that the maximum EDTA dose via inhalation of an aerosolized cosmetic formulation is below that shown to produce reproductive or developmental toxicity. Because of the potential to increase the penetration of other chemicals, formulators should continue to be aware of this when combining these ingredients with ingredients that previously have been determined to be safe, primarily because they were not significantly absorbed. Based on the available data, the Cosmetic Ingredient Review Expert Panel found that these ingredients are safe as used in cosmetic formulations.

PMID: unknown
Title: [Pseudothrombocytopenia].
Year: 1988
Abstract: 

PMID: unknown
Title: Addendum.
Year: 2016
Abstract: 

PMID: unknown
Title: [E.D.T.A].
Year: 1970
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

