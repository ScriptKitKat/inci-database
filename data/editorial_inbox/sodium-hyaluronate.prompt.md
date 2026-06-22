# Editorial prompt for: SODIUM HYALURONATE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `sodium-hyaluronate.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: SODIUM HYALURONATE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Final report of the safety assessment of hyaluronic acid, potassium hyaluronate, and sodium hyaluronate.
Year: 2009
Abstract: Hyaluronic acid, sodium hyaluronate, and potassium hyaluronate function in cosmetics as skin conditioning agents at concentrations up to 2%. Hyaluronic acid, primarily obtained from bacterial fermentation and rooster combs, does penetrate to the dermis. Hyaluronic acid was not toxic in a wide range of acute animal toxicity studies, over several species and with different exposure routes. Hyaluronic acid was not immunogenic, nor was it a sensitizer in animal studies. Hyaluronic acid was not a reproductive or developmental toxicant. Hyaluronic acid was not genotoxic. Hyaluronic acid likely does not play a causal role in cancer metastasis; rather, increased expression of hyaluronic acid genes may be a consequence of metastatic growth. Widespread clinical use of hyaluronic acid, primarily by injection, has been free of significant adverse reactions. Hyaluronic acid and its sodium and potassium salts are considered safe for use in cosmetics as described in the safety assessment.

PMID: unknown
Title: Crystalline sodium hyaluronate.
Year: 1958
Abstract: 

PMID: unknown
Title: Sodium Hyaluronate.
Year: 1984
Abstract: 

PMID: unknown
Title: Isolation of sodium hyaluronate.
Year: 1950
Abstract: 

PMID: unknown
Title: Sodium hyaluronate's effect on xerophthalmia: a meta-analysis of randomized controlled trials.
Year: 2016
Abstract: Several studies in the past have attempted to demonstrate the efficacy of sodium hyaluronate in the treatment of xerophthalmia. However, results have been conflicting and a definite conclusion has not yet been reached. In order to provide integrated evidence for the effectiveness of sodium hyaluronate and to judge the methodological value of relevant randomized controlled trials (RCTs) in nearly thirty years, we conducted this meta-analysis. A range of electronic databases were searched: MEDLINE, the Cochrane Library Database, EMBASE, CINAHL, Web of Science and the Chinese Biomedical Database (CBM) without language restrictions. Two independent reviewers assessed trials for eligibility and quality, and meta-analysis was performed using the STATA 12.0 software. An integrated odds ratio (OR) with its corresponding 95% confidence interval (95% CI) was calculated. Six RCTs were included with a total of 839 xerophthalmia patients. The meta-analysis results revealed that patients with xerophthalmia who received the intervention of sodium hyaluronate eye drops didn't have significantly higher remission rate of dry eye symptoms than those in controlled groups (OR = 1.811, 95% CI = 0.741-4.429, p = 0.193). Sensitivity analysis suggested that the statistical results were robust. No publication bias was detected in this meta-analysis (p > 0.05). Although sodium hyaluronate can be used to help relieve the symptoms of dry eyes, present evidence cannot show in unequivocal terms that patients with xerophthalmia can benefit more from the clinical application of sodium hyaluronate than other eye drops or therapies.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

