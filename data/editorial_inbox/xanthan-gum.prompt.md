# Editorial prompt for: XANTHAN GUM

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `xanthan-gum.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: XANTHAN GUM
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Xanthan gum in drug release.
Year: 2020
Abstract: Controlled release is of vital relevance for many drugs; thus, there is a keen interest in materials that can improve the release profiles of formulations administered via buccal, transdermal, ophthalmic, vaginal, and nasal. The desirable effects of those materials include the improvement of stability, adhesiveness, solubility, and retention time. Hence, different synthetic and natural polymers are utilized to achieve these objectives. In this respect, xanthan gum is an anionic polysaccharide that can be obtained from Xanthomonas bacteria. It is a natural polymer broadly employed in numerous food products, lotions, shampoos, and dermatological articles. Furthermore, due to its physicochemical features, xanthan gum is growingly utilized for the development and improvement of drug delivery systems. In this regard, encouraging findings have been revealed by recent formulations for pharmaceutical applications, including antiviral carriers, antibacterial transporters, transdermal patches, vaginal formulations, and anticancer medications. In this article, we perform a concise description of the chemical properties of xanthan gum and its role as a modifier of drug release. Furthermore, we present an outlook of the state of the art of research focused on the utilization of xanthan gum in varied pharmaceutical formulations, which include tablets, films, hydrogels, and nanoformulations. Finally, we discuss some perspectives about the use of xanthan gum in these formulations.

PMID: unknown
Title: Investigation of 3D-printed chitosan-xanthan gum patches.
Year: 2022
Abstract: In this study, using a new polymer combination of Chitosan(CH)/Xanthan Gum(XG) has been exhibited for wound dressing implementation by the 3D-Printing method, which was fabricated due to its biocompatible, biodegradable, improved mechanical strength, low degradation rate, and hydrophilic nature to develop cell-mimicking, cell adhesion, proliferation, and differentiation. Different concentrations of XG were added to the CH solution as 0.25, 0.50, 0.75, 1, and 2 wt% respectively in the formic acid/distilled water (1.5:8.5) solution and rheologically characterized to evaluate their printability. The results demonstrated that high mechanical strength, hydrophilic properties, and slow degradation rate were observed with the presence and increment of XG concentration within the 3D-Printed patches. Moreover, in vitro cell culture research was conducted by seeding NIH 3T3 fibroblast cells on the patches, proving the cell proliferation rate, viability, and adhesion. Finally, 1% XG and 4% CH containing 3D-Printed patches were great potential for wound dressing applications.

PMID: unknown
Title: Sources and methods of manufacturing xanthan by fermentation of various carbon sources.
Year: 2023
Abstract: Xanthan gum, an anionic polysaccharide with an exceptionally high molecular weight, is produced by the bacterium Xanthomonas sp. It is a versatile compound that has been utilized in various industries for decades. Xanthan gum was the second exopolysaccharide to be commercially produced, following dextran. In 1969, the US Food and Drug Administration (FDA) approved xanthan gum for use in the food and pharmaceutical industries. The food industry values xanthan gum for its exceptional rheological properties, which make it a popular thickening agent in many products. Meanwhile, the cosmetics industry capitalizes on xanthan gum's ability to form stable emulsions. The industrial production process of xanthan gum involves fermenting Xanthomonas in a medium that contains glucose, sucrose, starch, etc. as a substrate and other necessary nutrients to facilitate growth. This is achieved through batch fermentation under optimal conditions. However, the increasing costs of glucose in recent years have made the production of xanthan economically unviable. Therefore, many researchers have investigated alternative, cost-effective substrates for xanthan production, using various modified and unmodified raw materials. The objective of this analysis is to investigate how utilizing different raw materials can improve the cost-efficient production of xanthan gum.

PMID: unknown
Title: Interactions between xanthan gum and phenolic acids.
Year: 2024
Abstract: The molecular and colloidal-level interactions between two major phenolic acids, gallic and caffeic acid, with a major food polysaccharide, xanthan gum, were studied in binary systems aiming to correlate the stability of the binary systems as a function of pH and xanthan-polyphenol concentrations. Global stability diagrams were built, acting as roadmaps for examining the phase separation regimes followed by the fluorimetry-based thermodynamics of the interactions. The effects of noncovalent interactions on the macroscopic behavior of the binary systems were studied, using shear and extensional rheometry. The collected data for caffeic acid - xanthan gum mixtures showed that the main interactions were pH-independent volume exclusions, while gallic acid interacts with xanthan gum, especially at pH 7 with other mechanisms as well, improving the colloidal dispersion stability. A combination of fluorimetry, extensional rheology and stability measurements highlight the effect of gallic acid-induced aggregation of xanthan gum, both in structuring and de-structuring the binary systems. The above provide a coherent framework of the physicochemical aspect of binary systems, shedding light on the role of xanthan gum in its oral functions, such as in inducing texture, in model complex systems containing phenolic acids.

PMID: unknown
Title: Gum-based nanocomposites for the removal of metals and dyes from waste water.
Year: 2023
Abstract: The importance of water for all living organisms is unquestionable and protecting its sources is crucial. In order to reduce water contaminants, like toxic metals and organic dyes, researchers are exploring different techniques, such as adsorption, photocatalytic degradation, and electrolysis. Novel materials are also being sought. In particular, biopolymers like guar gum and xanthan gum, that are eco-friendly, non-toxic, reusable, abundant and cost-effective, have enormous potential. Gum-based nanocomposites can be prepared and used for removing heavy metals and colored dyes by adsorption and degradation, respectively. This review explains the significance of gum-based nanomaterials in waste water treatment, including preparative steps, characterization techniques, kinetics models, and the degradation and adsorption mechanisms involved.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

