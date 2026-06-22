# Editorial prompt for: TETRAHEXYLDECYL ASCORBATE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `tetrahexyldecyl-ascorbate.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: TETRAHEXYLDECYL ASCORBATE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Prospective randomized double-blind comparative study of topical acetyl zingerone with tetrahexyldecyl ascorbate versus tetrahexyldecyl ascorbate alone on facial photoaging.
Year: 2024
Abstract: Tetrahexydecyl ascorbate (THDA) is a lipophilic precursor to ascorbic acid that may be stabilized by acetyl zingerone (AZ). Studies have shown that the topical application of THDA may have photoprotective effects. Similarly, AZ has been shown to mitigate oxidative and inflammatory stress, thereby improving the appearance of photoaging. To examine the effects of THDA and AZ (THDA-AZ) on skin photoaging compared to THDA alone. In this double-blind, randomized controlled trial, healthy individuals aged 30 to 65 were included and 44 participants were randomized to receive either THDA-AZ (THDA 5% + AZ 1%) or THDA only (THDA 5%) for 8 weeks. Facial photographs were taken at 0, 4, and 8 weeks to analyze wrinkle severity, pigment intensity, and redness intensity. A skin colorimeter was used to assess infraorbital pigmentation and erythema. Self-perception of skin and tolerability were assessed through questionnaires. Average wrinkle severity was significantly decreased in the THDA-AZ group at Weeks 4 and 8 by 0.75% (p = 0.023) and 3.72% (p = 0.048), respectively, compared to the THDA group where wrinkle severity at Weeks 4 and 8 was increased by 7.88% and 4.48%, respectively. Facial pigment intensity was significantly decreased in the THDA-AZ group by 4.10% (p = 0.0002) at Week 8 compared to a 0.69% decrease in the THDA group. Facial redness intensity was decreased in the THDA-AZ group at Weeks 4 and 8 by 3.73% (p = 0.0162) and 14.25% (p = 0.045), respectively, compared to the THDA group where at Weeks 4 and 8 erythema increased by 27.5% and 8.34%, respectively. There were no significant differences in either group for infraorbital pigmentation or erythema. Daily use of combined THDA and AZ may improve facial wrinkle severity, pigment intensity, and erythema to a greater extent than THDA. While THDA alone increases facial wrinkle severity and erythema, the addition of AZ reduces both.

PMID: unknown
Title: Allergic contact dermatitis to two eye creams containing tetrahexyldecyl ascorbate.
Year: 2022
Abstract: 

PMID: unknown
Title: Tetrahexyldecyl Ascorbate (THDC) Degrades Rapidly under Oxidative Stress but Can Be Stabilized by Acetyl Zingerone to Enhance Collagen Production and Antioxidant Effects.
Year: 2021
Abstract: Tetrahexyldecyl Ascorbate (THDC) is an L-ascorbic acid precursor with improved stability and ability to penetrate the epidermis. The stability and transdermal penetration of THDC, however, may be compromised by the oxidant-rich environment of human skin. In this study, we show that THDC is a poor antioxidant that degrades rapidly when exposed to singlet oxygen. This degradation, however, was prevented by combination with acetyl zingerone (AZ) as a stabilizing antioxidant. As a standalone ingredient, THDC led to unexpected activation of type I interferon signaling, but this pro-inflammatory effect was blunted in the presence of AZ. Moreover, the combination of THDC and AZ increased expression of genes associated with phospholipid homeostasis and keratinocyte differentiation, along with repression of

PMID: unknown
Title: Usage Frequency and Ecotoxicity of Skin Depigmenting Agents.
Year: 2025
Abstract: 

PMID: unknown
Title: Open-label topical application of tetrahexyldecyl ascorbate and acetyl zingerone containing serum improves the appearance of photoaging and uneven pigmentation.
Year: 2024
Abstract: Skin photoaging and uneven pigmentation are common dermatological concerns. Tetrahexyldecyl ascorbate (THDA) and acetyl zingerone (AZ) are potent antioxidants that have been shown to have anti-photoaging and anti-pigmentation effects. THDA is a more stable and penetrable form of vitamin C. AZ is an antioxidant derived from ginger which has clinical evidence for improving photoaging. However, no studies have assessed how they may synergistically act on the skin. This study aims to assess whether a serum containing both THDA and AZ can improve photoaging and the appearance of uneven facial pigmentation. This open-label study was conducted on 35 healthy individuals aged 21-55. All subjects were instructed to use three to five drops of the topical serum (Power-C Serum, Image Skincare, Lantana, FL) daily for 12 weeks. Videomicroscopy and high-resolution photography and various skin biophysical measurements were taken at baseline, 1, 4, and 12 weeks. Outcomes included skin tone and pigmentation, transepidermal water loss (TEWL), skin smoothness, firmness, and elasticity. Compared to baseline, the results at 12 weeks revealed significant decreases in skin pigmentation (p < 0.0001), decreased fine lines and wrinkles (p < 0.0001), and increased smoothness (p < 0.0001), firmness (p < 0.0001), and elasticity (p < 0.0001). Additionally, transepidermal water loss was significantly decreased at 4 weeks compared to baseline (p = 0.01), indicating an increased epidermal barrier integrity. Overall, these findings provide evidence for the combined use of THDA and AZ to address skin photoaging and dyspigmentation changes.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

