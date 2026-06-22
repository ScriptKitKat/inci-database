# Editorial prompt for: ASCORBYL GLUCOSIDE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `ascorbyl-glucoside.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: ASCORBYL GLUCOSIDE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Safety Assessment of Ascorbyl Glucoside and Sodium Ascorbyl Glucoside as Used in Cosmetics.
Year: 2025
Abstract: The Expert Panel for Cosmetic Ingredient Safety (Panel) reviewed the safety of Ascorbyl Glucoside and Sodium Ascorbyl Glucoside in cosmetic products. These ingredients are reported to have the following functions in cosmetics: antioxidant, and skin-conditioning agent-miscellaneous. The Panel reviewed data relevant to the safety of these ingredients in cosmetic formulations, and concluded that Ascorbyl Glucoside and Sodium Ascorbyl Glucoside are safe in cosmetics in the present practices of use and concentration described in this safety assessment.

PMID: unknown
Title: Treatment with Ascorbyl Glucoside-Arginine Complex Ameliorates Solar Lentigos.
Year: 2024
Abstract: Little is known about the anti-pigmenting effects of skin-whitening agents on solar lentigos (SLs). To characterize the anti-pigmenting effects of a newly designed derivative ascorbyl glucoside-arginine complex (AGAC) on SLs, lotions with or without 28% AGAC were applied twice daily for 24 weeks in a double-blind half-face study of 27 Japanese females with SLs. The pigmentation scores and skin colors of previously selected SLs on the right and left sides of the faces of the subjects were evaluated using a photo-scale, a color difference meter and a Mexameter. Treatment with the test lotion elicited a significant decrease in pigmentation scores at 24 weeks compared to week 0, with a significant decrease in pigmentation scores at 24 weeks compared to the placebo lotion. In the test lotion-treated SLs, the lightness (L) and melanin index (MI) values that reflect the pigmentation level significantly increased and decreased, respectively, at 12 and 24 weeks of treatment compared to week 0. Comparisons of increased L values or decreased MI values between the test and placebo lotion-treated SLs demonstrated that the test lotion-treated SLs had significantly higher increased L or decreased MI values than the placebo lotion-treated SLs both at 12 and 24 weeks of treatment. The sum of our results strongly indicates that AGAC is distinctly effective in ameliorating the hyperpigmentation levels of SLs at a level visibly recognizable by the subjects, without any hypo-pigmenting effects or skin problems.

PMID: unknown
Title: Nutritional Properties and significance of vitamin glycosides.
Year: 1998
Abstract: Glycosylated forms of pyridoxine, vitamin D, niacin, pantothenate, and riboflavin exist in nature, whereas glycosides of retinol and ascorbic acid are products of in vitro transglycosidation. Beta-Glucosides of pyridoxine (a) are prevalent in plant-derived foods, (b) contribute to human nutrition as partially available sources of vitamin B6, (c) undergo partial hydrolysis by a novel mammalian cytosolic beta-glucosidase, and (d) exert a weak antagonistic effect on the utilization of free pyridoxine. Niacin exists in grains as complexed forms with low bioavailability, whereas vitamin D glycosides are toxic components of certain calcinogenic plants of importance in animal health. Glycosides of pantothenate and riboflavin appear to be minor products of mammalian metabolism. Glycosylation of retinol or other hydrophobic alcohols may facilitate glycolipid turnover, whereas a stable ascorbyl glucoside may have nutritional applications. Glycosylation of vitamins exerts widely ranging chemical and biological effects, with great nutritional and metabolic significance.

PMID: unknown
Title: Sage extract and ascorbic acid derivative inhibit melanogenesis via downregulating keratinocyte-derived GM-CSF.
Year: 2025
Abstract: Salvia officinalis (sage) extract has demonstrated potential as a functional ingredient for skin care application. However, its effect and mechanism in regulating skin pigmentation remain largely unclear. This study investigated the effects of sage ethanol extract (SGE) on melanogenesis and its underlying molecular mechanisms. Treatment with SGE in a human skin equivalent model (3D-skin) suppressed melanin production. To clarify the mechanism of action, the study focused on senescence-associated secretory phenotype (SASP) factors, which are implicated in age-related pigmentation changes. q-PCR and ELISA analyses showed that SGE inhibits melanogenesis by suppressing the expression of granulocyte-macrophage colony-stimulating factor (GM-CSF), a known SASP factor in keratinocytes. Interestingly, a similar effect was observed with L-ascorbic acid 2-glucoside (AG), previously identified as a tyrosinase inhibitor. Importantly, p38 and JNK MAP-kinase were identified as upstream regulators of GM-CSF that are suppressed by SGE. These findings provide new insights into how SGE and AG regulate pigmentation via keratinocyte-derived GM-CSF, highlighting their potential in modulating skin tone and pigmentation through cellular signaling pathways.

PMID: unknown
Title: Functions, applications and production of 2-O-D-glucopyranosyl-L-ascorbic acid.
Year: 2012
Abstract: Vitamin C (VC) is an essential nutrient that cannot be synthesized by the human body. Due to its extreme instability, various VC derivatives have been developed in an attempt to improve stability while retaining the same biological activity. One of the most important VC derivatives, 2-O-D-glucopyranosyl-L-ascorbic acid (AA-2G), has attracted increasing attention in recent years with a wide range of applications in cosmetics, food, and medicine. In this mini-review, we first introduce the types and properties of different VC glycosyl derivatives. Next, we provide an overview of the functions and applications of AA-2G. Finally, we discuss in-depth the current status and future prospects of AA-2G production by biotransformation.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

