# Editorial prompt for: ETHYLHEXYL METHOXYCINNAMATE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `ethylhexyl-methoxycinnamate.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: ETHYLHEXYL METHOXYCINNAMATE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Review of environmental effects of oxybenzone and other sunscreen active ingredients.
Year: 2019
Abstract: With increasing awareness regarding the risks of sunburn, photoaging, and skin cancer, the use of sunscreens has increased. Organic and inorganic filters are used in sunscreen products worldwide. Concerns have been raised regarding the environmental effects of commonly used organic ultraviolet (UV) filters, including oxybenzone (benzophenone-3), 4-methylbenzylidene camphor, octocrylene, and octinoxate (ethylhexyl methoxycinnamate). Studies have identified UV filters such as oxybenzone, octocrylene, octinoxate, and ethylhexyl salicylate in almost all water sources around the world and have commented that these filters are not easily removed by common wastewater treatment plant techniques. Additionally, in laboratory settings, oxybenzone has been implicated specifically as a possible contributor to coral reef bleaching. Furthermore, UV filters such as 4-methylbenzylidene camphor, oxybenzone, octocrylene, and octinoxate have been identified in various species of fish worldwide, which has possible consequences for the food chain. As dermatologists, it is important for us to continue to emphasize the public health impact of excessive sun exposure and advise our patients about proper photoprotection practice, which consists of seeking shade, wearing photoprotective clothing (including hats and sunglasses), and applying appropriate sunscreens.

PMID: unknown
Title: Facial disbiosis and UV filters.
Year: 2024
Abstract: Acne is a multifactorial inflammatory disease with a robust microbial component and numerous correlations with dysbiosis states. Furthermore, various factors are recognized as triggers for skin dysbiosis, including the use of certain cosmetics. Based on these arguments, we hypothesized that using photoprotective formulations could trigger dysbiosis and the occurrence of acne manifestations. To verify this assumption, six volunteers between 19 and 23 years of age, meeting all the inclusion criteria, received two applications a day of a non-commercial sunscreen formulation developed with the sun filters ethylhexyl methoxycinnamate, ethylhexyl salicylate, methyl anthranilate, and octocrylene dispersed in a base gel, with an estimated protection factor of 28.8. The pure base gel was used as a control. The samples were applied to an area delimited by a standard template (15 cm

PMID: unknown
Title: Ethylhexyl methoxycinnamate and butyl methoxydibenzoylmethane: Toxicological effects on marine biota and human concerns.
Year: 2022
Abstract: Ethylhexyl methoxycinnamate (EHMC) (CAS number: 5466-77-3) and butyl methoxydibenzoylmethane (BMDM) (CAS number: 70356-09-1) are important sunscreens. However, frequent application of large amounts of these compounds may reflect serious environmental impact, once it enters the environment through indirect release via wastewater treatment or immediate release during water activities. In this article, we reviewed the toxicological effects of EHMC and BMDM on aquatic ecosystems and the human consequences. According to the literature, EHMC and BMDM have been detected in water samples and sediments worldwide. Consequently, these compounds are also present in several marine organisms like fish, invertebrates, coral reefs, marine mammals, and other species, due to its bioaccumulation potential. Studies show that these chemicals are capable of damaging the aquatic beings in different ways. Further, bioaccumulation studies have shown that EHMC biomagnifies through trophic levels, which makes human seafood consumption a concern because the higher position in the trophic chain, the more elevate levels of ultraviolet (UV) filters are detected, and it is established that EHMC present adverse effects on the human organism. In contrast, there are no studies on the BMDM bioaccumulation and biomagnification potential. Different strategies can be adopted to avoid the damage caused by sunscreens in the environment and human organism. Two of them include the use of natural photoprotectors, such as polyphenols, in association with UV filters in sunscreens and the development of new and safer UV filters. Overall, this review shows the importance of studying the impacts of sunscreens in nature and developing safer sunscreens and formulations to safeguard marine fauna, ecosystems, and humans.

PMID: unknown
Title: A review of environmental occurrence and toxicity of 2-ethylhexyl salicylate, homomenthyl salicylate and ethylhexyl methoxycinnamate.
Year: 2026
Abstract: 2-Ethylhexyl salicylate (EHS), homomenthyl salicylate (HMS), and ethylhexyl methoxycinnamate (EHMC) are three commonly used organic ultraviolet filters (OUVFs) that exhibit environmental persistence and bioaccumulation potential. They are widely distributed in surface water, wastewater, sediment, soil, air, and dust, as well as in organisms. Their concentrations vary significantly across matrices, spatiotemporal scales, and species. In surface water, the concentrations of the three OUVFs are notably higher in industrial and tourist-influenced waters, with the mean concentration of HMS reaching 215.4 ng/L at Waikiki Beach and EHS averaging 203 ng/L along Romania's Black Sea coast. In wastewater, EHMC occurred at hundreds of ng/L in the dissolved phase, while its particulate-phase concentration peaked at 65,500 ng/g. Their atmospheric concentrations are predominantly in the pg/m

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

