# Editorial prompt for: ALPHA-ARBUTIN

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `alpha-arbutin.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: ALPHA-ARBUTIN
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Drug design of tyrosinase inhibitors.
Year: 2024
Abstract: This copper-containing enzyme catalyzes the rate-limiting step for the melanin skin pigment bioproduction. Tyrosinase inhibitors can be exploited as skin whitening agents and food preservatives, opening new scenarios in food, cosmetics, agriculture and medicine. Despite the availability of natural inhibitors (hydroquinone, α-arbutin, kojic acid, retinoids, azelaic acid, resveratrol, caftaric acid, valonea tannin, chrysosplenetin and phenylethyl resorcinol), several synthetic compounds were proposed to overcome side effects and to improve the efficacy of natural agents. This chapter will gather the recent advances about synthetic tyrosinase inhibitors from the MedChem perspective, providing new suggestions for the scaffold-based design of innovative compounds.

PMID: unknown
Title: Recent progress on biological production of α-arbutin.
Year: 2018
Abstract: Arbutin, a glucoside of hydroquinone, is used as a powerful skin lightening agent in the cosmeceutical industry because of its strong inhibitory effect on the human tyrosinase activity. It is a natural compound occurring in a number of plants, with a β-anomeric form of the glycoside bond between glucose and hydroquinone. α-Arbutin, which glycoside bond is generated with α-anomeric form, is the isomer of natural arbutin. α-Arbutin is generally produced by transglucosylation of hydroquinone by microbial glycosyltransferases. It is interesting that α-arbutin is found to be over 10 times more effective than arbutin, and thus biological production of α-arbutin attracts increasing attention. Seven different microbial enzymes have been identified to be able to produce α-arbutin, including α-amylase, sucrose phosphorlase, cyclodextrin glycosyltransferase, α-glucosidase, dextransucrase, amylosucrase, and sucrose isomerase. In this work, enzymatic and microbial production of α-arbutin is reviewed in detail.

PMID: unknown
Title: [Research progress in biosynthesis of arbutin].
Year: 2024
Abstract: Arbutin, a glycosylated compound of hydroquinone, exists in two forms of β-arbutin and α-arbutin based on the configuration of the glycosidic bond. As a safe and stable whitening agent, arbutin is widely used in cosmetics, and it has antioxidant, antimicrobial, anti-inflammatory, and anti-tumor activities. The production of arbutin by plant extraction faces challenges such as long plant growth periods, complex extraction processes, and low yields. The chemical synthesis of arbutin suffers from harsh reaction conditions, poor stereo-selectivity, and low yields. In recent years, biosynthesis emerges as the most popular method to produce arbutin because of the simple and mild reaction conditions, low costs, and environmental friendliness. This review summarizes the research progress in four biosynthetic strategies for arbutin, including plant conversion, enzyme catalysis, whole-cell catalysis, and microbial fermentation. The advantages and limitations of these biosynthetic strategies are discussed, and future research directions are proposed.

PMID: unknown
Title: A comprehensive review of the therapeutic potential of α-arbutin.
Year: 2021
Abstract: Cosmetic dermatology preparations such as bleaching agents are ingredients with skin-related biological activities for increasing and improving skin beauty. The possibility of controlling skin hyperpigmentation disorders is one of the most important research goals in cosmetic preparations. Recently, cosmetics containing herbal and botanical ingredients have attracted many interests for consumers of cosmetic products because these preparations are found safer than other preparations with synthetic components. However, high-quality trial studies in larger samples are needed to confirm safety and clinical efficacy of phytotherapeutic agents with high therapeutic index. Arbutin (p-hydroxyphenyl-β-d-glucopyranoside) is a bioactive hydrophilic polyphenol with two isomers including alpha-arbutin (4-hydroxyphenyl-α-glucopyranoside) and β-arbutin (4-hydroxyphenyl-β-glucopyranoside). It is used as a medicinal plant in phytopharmacy. Studies have shown that alpha-arbutin is 10 times more effective than natural arbutin. A comparison of IC50 values showed that α-arbutin (with concentration 2.0 mM) has a more potent inhibitory activity on human tyrosinase against natural arbutin (with higher concentration than 30 mM). A review of recent studies showed that arbutin could be beneficial in treatment of various diseases such as hyperpigmentation disorders, types of cancers, central nervous system disorders, osteoporosis, diabetes, etc. This study was designed to describe the therapeutic efficiencies of arbutin.

PMID: unknown
Title: The Effect of α-Arbutin on UVB-Induced Damage and Its Underlying Mechanism.
Year: 2024
Abstract: Ultraviolet radiation can heighten tyrosinase activity, stimulate melanocyte production, impede the metabolism of numerous melanocytes, and result in the accumulation of plaques on the skin surface. α-Arbutin, a bioactive substance extracted from the arbutin plant, has been widely used for skin whitening. In this study, the whitening effect of α-arbutin by inhibiting tyrosinase activity and alleviating the photoaging effect induced by UVB are investigated. The results indicate that α-arbutin can inhibit skin inflammation, and its effectiveness is positively correlated with concentration. Moreover, α-arbutin can reduce the skin epidermal thickness, decrease the number of inflammatory cells, and down-regulate the expression levels of IL-1β, IL-6 and TNF-α, which are inflammatory factors. It also promotes the expression of COL-1 collagen, thus playing an important role in anti-inflammatory action. Network pharmacology, metabolomics and transcriptomics further confirm that α-arbutin is related to the L-tyrosine metabolic pathway and may interfere with various signaling pathways related to melanin and other photoaging by regulating metabolic changes. Therefore, α-arbutin has a potential inhibitory effect on UVB-induced photoaging and possesses a whitening effect as a cosmetic compound.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

