# Editorial prompt for: GLYCOLIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `glycolic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: GLYCOLIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Basic chemical peeling: Superficial and medium-depth peels.
Year: 2019
Abstract: Chemical peeling, or chemexfoliation, has been used for centuries to improve signs of ultraviolet light-induced sun damage. Over the last 30 years, the science behind chemical peeling has evolved, increasing our understanding of the role of peeling ingredients and treatment indications. The depth of peels is directly related to improved results and to the number of complications that can occur. Key principles for superficial and medium depth peeling are discussed, as well as appropriate indications for these treatments.

PMID: unknown
Title: Chemical Peels for Melasma: A Systematic Review.
Year: 2024
Abstract: Melasma is a common chronic, relapsing pigmentary disorder that causes psychological impact. Chemical peels are a well-known therapeutic modality used for accelerating the treatment of melasma. To review the published evidence on the efficacy and safety of chemical peels in the treatment of melasma. A systematic review was done. A meta-analysis could not be done due to the heterogeneity of data. The authors conducted a PubMed search and included prospective case series of more than 10 cases and randomized controlled trials (RCTs) that have studied the safety and/or efficacy of chemical peel in melasma. Out of 24 studies, 9 were clinical/comparative trials and 15 were RCTs. The total sample size was 1,075. The duration of the study varied from 8 to 36 weeks. Only 8 studies were split face. All studies used self-assessment, physician global assessment, and Melasma Area and Severity Index (MASI) for quantifying the results. Glycolic acid was found to be the most safe and effective in melasma. Chemical peels were found to be safe and effective in the management of melasma.

PMID: unknown
Title: Glycolic acid peels.
Year: 1996
Abstract: 

PMID: unknown
Title: Glycolic acid and D-lactate-putative products of DJ-1-restore neurodegeneration in FUS - and SOD1-ALS.
Year: 2024
Abstract: Amyotrophic lateral sclerosis (ALS) leads to death within 2-5 yr. Currently, available drugs only slightly prolong survival. We present novel insights into the pathophysiology of

PMID: unknown
Title: Complete Restoration of Hearing Loss and Cochlear Synaptopathy via Minimally Invasive, Single-Dose, and Controllable Middle Ear Delivery of Brain-Derived Neurotrophic Factor-Poly(dl-lactic acid-
Year: 2024
Abstract: Noise-induced hearing loss (NIHL) often accompanies cochlear synaptopathy, which can be potentially reversed to restore hearing. However, there has been little success in achieving complete recovery of sensorineural deafness using nearly noninvasive middle ear drug delivery before. Here, we present a study demonstrating the efficacy of a middle ear delivery system employing brain-derived neurotrophic factor (BDNF)-poly-(dl-lactic acid-

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

