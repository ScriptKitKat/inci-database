# Editorial prompt for: POTASSIUM SORBATE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `potassium-sorbate.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: POTASSIUM SORBATE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Alkylating potential of potassium sorbate.
Year: 2005
Abstract: A kinetic study of the alkylating potential of potassium sorbate (S)-a food preservative used worldwide-in 7:3 water/dioxane medium was performed. The following conclusions were drawn: (i) Potassium sorbate shows alkylating activity on the nucleophile 4-(p-nitrobenzyl)pyridine (NBP), a trap for alkylating agents with nucleophilic characteristics similar to those of DNA bases, (ii) The NBP alkylation reaction complies with the rate equation r = k(alk)[H+][S][NBP]/(K(a) + [H+]), K(a) being the sorbic acid dissociation constant and k(alk) the rate constant of NBP alkylation by the undissociated acid. In the range of pH 5-6, the alkylation time ranges between 18 days (pH 5.2) and >1 month (pH > or = 6). (iii) NBP alkylation occurs through a reaction with deltaH# = 78 kJ mol(-1), which is much higher than those of NBP alkylation by stronger alkylating agents. (iv) The absorption coefficient of the sorbate-NBP adduct was determined to be epsilon = 204 M(-1) cm(-1) (lambda = 580 nm), this value being rationalized in terms of the adduct structure. (v) The results can help to establish suitable expiration times for products preserved with potassium sorbate.

PMID: unknown
Title: Associations between preservative food additives and type 2 diabetes incidence in the NutriNet-Santé prospective cohort.
Year: 2026
Abstract: Experimental studies suggested potential adverse effects of preservative food additives, but epidemiological data are lacking. We aim to investigate associations between exposure to these compounds and type 2 diabetes incidence in the NutriNet-Santé prospective cohort (n = 108,723; 79.2%women; mean age=42.5 (SD = 14.6); France, 2009-2023). Dietary intakes are assessed using repeated 24h-dietary records. Exposure is evaluated through multiple composition databases and ad-hoc laboratory assays in food matrices. Associations between cumulative exposures to preservatives and diabetes incidence are characterised using multi-adjusted Cox models. The sum of total preservatives encompasses 58 substances. Among those, 17 are consumed by at least 10% of the study population and thus individually investigated. Thirteen (12 after multiple test correction) widely used individual preservatives are associated with higher diabetes incidence (n=1131cases): potassium sorbate, potassium metabisulfite, sodium nitrite, acetic, citric and phosphoric acids, sodium acetates, calcium propionate, sodium ascorbate, alpha-tocopherol, sodium erythorbate, and rosemary extracts. These findings call for their safety re-evaluation and support recommendations to favour fresh and minimally processed foods without superfluous additives. Trial registration: The NutriNet-Santé cohort is registered at clinicaltrials.gov (NCT03335644).

PMID: unknown
Title: Potassium-doped g-C
Year: 2023
Abstract: Element doping is recognized as an efficient method to boost the photocatalytic performance of photocatalysts. Here, a new potassium ion-doped precursor, potassium sorbate, was employed in melamine configuration during calcination process to prepare the potassium-doped g-C

PMID: unknown
Title: The genotoxicity status of sorbic acid, potassium sorbate and sodium sorbate.
Year: 1992
Abstract: 

PMID: unknown
Title: A Comfort Survey of Timolol Hemihydrate 0.5% Solution Once or Twice Daily vs Timolol Maleate in Sorbate.
Year: 2013
Abstract: To evaluate by survey the comfort upon instillation of timolol hemihydrate compared to timolol maleate with potassium sorbate. A prospective, multicenter, observational, non-interventional study. One hundred and three patients of open-angle glaucoma or ocular hypertension who were ≥21 years old and were currently prescribed timolol hemihydrate (once or twice daily) or timolol maleate with potassium sorbate once daily as monotherapy or as a part of two-drug therapy. Study was performed at seven clinical sites in the United States. Patients were surveyed on comfort upon instillation of timolol hemihydrate compared to timolol maleate with potassium sorbate. A difference between timolol hemihydrate and timolol maleate with potassium sorbate for questions 1 (burning/stinging on instillation, p < 0.001) and 4 (tearing on instillation, p = 0.024) was noted. There were no differences between treatment groups for any other question (p > 0.05). This survey suggests that timolol hemihydrate is associated with less stinging/burning and tearing than timolol maleate with potassium sorbate. How to cite this article: Stewart WC, Oehler JC, Choplin NT, Markoff JI, Moster MR, Ichhpujani P, Nelson LA. A Comfort Survey of Timolol Hemihydrate 0.5% Solution Once or Twice Daily vs Timolol Maleate in Sorbate. J Current Glau Prac 2013;7(1):11-16.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

