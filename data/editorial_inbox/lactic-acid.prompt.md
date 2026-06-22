# Editorial prompt for: LACTIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `lactic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: LACTIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: The role of lactic acid production by probiotic Lactobacillus species in vaginal health.
Year: 2017
Abstract: Vaginal eubiosis is characterised by beneficial lactobacillus-dominated microbiota. In contrast, vaginal dysbiosis (e.g. bacterial vaginosis, BV), characterised by an overgrowth of multiple anaerobes, is associated with an increased risk of adverse urogenital and reproductive health outcomes. A major distinguishing feature between the vaginal environment in states of eubiosis and dysbiosis is a high concentration of lactic acid, produced by lactobacilli, that acidifies the vagina in eubiosis versus a sharp drop in lactic acid and an increase in pH in dysbiosis. Here we review the antimicrobial, antiviral and immunomodulatory properties of lactic acid and the use of lactic acid and lactobacilli probiotics in preventing or treating BV.

PMID: unknown
Title: Lactic acid fermentation of osmo-dehydrated onion.
Year: 2023
Abstract: The aim of the study was to determine the effect of osmoconcentration in a sucrose and sodium chloride solution on the efficiency of lactic fermentation and the content of polyphenols and oligosaccharides in yellow and red onion varieties: Alonso, Hysky, Hystore, and Red Lady. In most cases, no negative effect of onion dehydration was noted on the growth or number of the bacteria tested. Osmotic dehydration of onions prior to lactic fermentation may positively modify the profile of lactic acid isomers by increasing the proportion of the L (+) isomer. The use of osmotic dehydration before fermentation did not adversely affect the content of polyphenols in the onions. Simultaneously, the loss of fructo-oligosaccharides was limited: 60 % of the initial fructo-oligosaccharide content was obtained using the Alonso cultivar and Levilactobacillus brevis 0944 for onion fermentation.

PMID: unknown
Title: Biosynthesis of D-lactic acid from lignocellulosic biomass.
Year: 2018
Abstract: D-lactic acid is a versatile and important industrial chemical that can be applied in the synthesis of thermal-resistant poly-lactic acid. Biosynthesis of D-lactic acid can be achieved by a variety of microorganisms, including lactic acid bacteria, yeast, and fungi; however, the final product yield, optical purity, and the utilization of both glucose and xylose are restricted. Consequently, engineered microbial systems are essential to attain high titer, productivity, and complete utilization of sugars. Herein, we critically evaluate the promising wild-type microorganisms, as well as genetically modified microorganisms to produce enantiomerically pure D-lactic acid, particularly from renewable lignocellulosic biomass. In addition, innovative bioreactor operation, metabolic flux analysis, and recent genetic engineering methods for targeted microbial D-lactic acid synthesis will be discussed.

PMID: unknown
Title: Recent Advances in Lactic Acid Production by Lactic Acid Bacteria.
Year: 2021
Abstract: Lactic acid can synthesize high value-added chemicals such as poly lactic acid. In order to further minimize the cost of lactic acid production, some effective strategies (e.g., effective mutagenesis and metabolic engineering) have been applied to increase productive capacity of lactic acid bacteria. In addition, low-cost cheap raw materials (e.g., cheap carbon source and cheap nitrogen source) are also used to reduce the cost of lactic acid production. In this review, we summarized the recent developments in lactic acid production, including efficient strain modification technology (high-efficiency mutagenesis means, adaptive laboratory evolution, and metabolic engineering), the use of low-cost cheap raw materials, and also discussed the future prospects of this field, which could promote the development of lactic acid industry.

PMID: unknown
Title: Lactic acid bacteria: life after genomics.
Year: 2011
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

