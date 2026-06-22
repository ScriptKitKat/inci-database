# Editorial prompt for: OCTOCRYLENE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `octocrylene.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: OCTOCRYLENE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Review of environmental effects of oxybenzone and other sunscreen active ingredients.
Year: 2019
Abstract: With increasing awareness regarding the risks of sunburn, photoaging, and skin cancer, the use of sunscreens has increased. Organic and inorganic filters are used in sunscreen products worldwide. Concerns have been raised regarding the environmental effects of commonly used organic ultraviolet (UV) filters, including oxybenzone (benzophenone-3), 4-methylbenzylidene camphor, octocrylene, and octinoxate (ethylhexyl methoxycinnamate). Studies have identified UV filters such as oxybenzone, octocrylene, octinoxate, and ethylhexyl salicylate in almost all water sources around the world and have commented that these filters are not easily removed by common wastewater treatment plant techniques. Additionally, in laboratory settings, oxybenzone has been implicated specifically as a possible contributor to coral reef bleaching. Furthermore, UV filters such as 4-methylbenzylidene camphor, oxybenzone, octocrylene, and octinoxate have been identified in various species of fish worldwide, which has possible consequences for the food chain. As dermatologists, it is important for us to continue to emphasize the public health impact of excessive sun exposure and advise our patients about proper photoprotection practice, which consists of seeking shade, wearing photoprotective clothing (including hats and sunglasses), and applying appropriate sunscreens.

PMID: unknown
Title: Review of the safety of octocrylene used as an ultraviolet filter in cosmetics.
Year: 2019
Abstract: Octocrylene or octocrilene is an organic ultraviolet (UV) filter which absorbs mainly UVB radiation and short UVA wavelengths. It is used in various cosmetic products to either provide an appropriate sun protection factor in sunscreen products or to protect cosmetic formulations from UV radiation. There is no discussion that UV filters are beneficial ingredients in cosmetics since they protect from skin cancer, but octocrylene has been recently incriminated to potentially induce adverse effects on the endocrine system in addition to having allergic and/or photoallergic potential. However, the substance has the advantage to work synergistically with other filters allowing a beneficial broad photoprotection, e.g. it stabilizes the UVA filter avobenzone (i.e. butylmethoxydibenzoylmethane). Like all chemicals used in cosmetics, the safety profile of octocrylene is constantly under assessment by the European Chemical Agency (ECHA) since it has been registered according to the European regulation Registration, Evaluation, Authorisation and Restriction of Chemicals. Summaries of safety data of octocrylene are publicly available on the ECHA website. This review aims to present the main safety data from the ECHA website, as well as those reported in scientific articles from peer-reviewed journals. The available data show that octocrylene does not have any endocrine disruption potential. It is a rare sensitizer, photocontact allergy is more frequent and it is considered consecutive to photosensitization to ketoprofen. Based on these results, octocrylene can be considered as safe when used as a UV filter in cosmetic products at a concentration up to 10%.

PMID: unknown
Title: Ultraviolet Filters: Dissecting Current Facts and Myths.
Year: 2024
Abstract: Skin cancer is a global and increasingly prevalent issue, causing significant individual and economic damage. UV filters in sunscreens play a major role in mitigating the risks that solar ultraviolet ra-diation poses to the human organism. While empirically effective, multiple adverse effects of these compounds are discussed in the media and in scientific research. UV filters are blamed for the dis-ruption of endocrine processes and vitamin D synthesis, damaging effects on the environment, induction of acne and neurotoxic and carcinogenic effects. Some of these allegations are based on scientific facts while others are simply arbitrary. This is especially dangerous considering the risks of exposing unprotected skin to the sun. In summary, UV filters approved by the respective governing bodies are safe for human use and their proven skin cancer-preventing properties make them in-dispensable for sensible sun protection habits. Nonetheless, compounds like octocrylene and ben-zophenone-3 that are linked to the harming of marine ecosystems could be omitted from skin care regimens in favor of the myriad of non-toxic UV filters.

PMID: unknown
Title: Sunscreens.
Year: 2014
Abstract: Sunscreens have become since more than 40 years the most popular means of protection against UV radiation (UVR) in Western countries. Organic and inorganic filters with different absorption spectrum exist. They filter or scatter UVR. Protection from UVB is quantified as a minimal erythema dose-based sun protection factor. UVA protection testing is less standardized: Persistent pigment darkening and critical wavelength are currently used methods. Marketing and labeling of sunscreens underlay national regulation which explains major differences between the European and the US sunscreen market. Sunscreens are most performing in sunburn prevention. Broad spectrum UVB and UVA protection and regular application in sufficient amounts are essential for prevention of skin cancers, UV-induced immunosuppression, and skin aging. A significant benefit from regular sunscreen use has not yet been demonstrated for primary prevention of basal cell carcinoma and melanoma. Concerning the prevention of actinic keratoses, squamous cell carcinomas, and skin aging, the effect of sunscreens is significant, but it remains incomplete. Some organic UV filters (PABA derivatives, cinnamates, benzophenones, and octocrylene) have been described to cause photoallergy. Percutaneous absorption and endocrine disrupting activity of small-sized organic and nano-sized inorganic UV filters have been reported. On lesional skin and in pediatric settings, these products should be used with caution. Cutaneous vitamin D synthesis depending on skin-carcinogenic UVB radiation, the potential risk of vitamin D deficiency by sunscreen use has become a major subject of public health debate. Sunscreens indeed impair vitamin D synthesis if they are used in the recommended amount of 2 mg/cm2, but not in lesser thickness below 1.5 mg/cm2 that corresponds better to what users apply in real life conditions. Large molecular last generation UVB-UVA broad spectrum sunscreens have a better benefit-risk ratio than former organic filters: They offer better protection in the UVA band, they are non toxic and non allergenic. A better outcome of sunscreen efficacy especially in primary skin cancer prevention may be achieved with these molecules.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

