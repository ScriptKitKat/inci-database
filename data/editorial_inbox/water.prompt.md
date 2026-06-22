# Editorial prompt for: WATER

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `water.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: WATER
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Water as an essential nutrient: the physiological basis of hydration.
Year: 2010
Abstract: How much water we really need depends on water functions and the mechanisms of daily water balance regulation. The aim of this review is to describe the physiology of water balance and consequently to highlight the new recommendations with regard to water requirements. Water has numerous roles in the human body. It acts as a building material; as a solvent, reaction medium and reactant; as a carrier for nutrients and waste products; in thermoregulation; and as a lubricant and shock absorber. The regulation of water balance is very precise, as a loss of 1% of body water is usually compensated within 24 h. Both water intake and water losses are controlled to reach water balance. Minute changes in plasma osmolarity are the main factors that trigger these homeostatic mechanisms. Healthy adults regulate water balance with precision, but young infants and elderly people are at greater risk of dehydration. Dehydration can affect consciousness and can induce speech incoherence, extremity weakness, hypotonia of ocular globes, orthostatic hypotension and tachycardia. Human water requirements are not based on a minimal intake because it might lead to a water deficit due to numerous factors that modify water needs (climate, physical activity, diet and so on). Water needs are based on experimentally derived intake levels that are expected to meet the nutritional adequacy of a healthy population. The regulation of water balance is essential for the maintenance of health and life. On an average, a sedentary adult should drink 1.5 l of water per day, as water is the only liquid nutrient that is really essential for body hydration.

PMID: unknown
Title: Water-aided colonoscopy.
Year: 2013
Abstract: Water-aided methods for colonoscopy include the established water immersion and the recent novel modification of water exchange. Water immersion entails the use of water as an adjunct to air insufflations to facilitate insertion. Water exchange evolved from water immersion to facilitate completion of colonoscopy without discomfort in unsedated patients. Infused water is removed predominantly during insertion rather than withdrawal. A higher adenoma detection rate has been reported with water exchange. Aggregate data of randomized controlled trials suggest that water exchange may be superior to water immersion in attenuating colonoscopy discomfort and optimizing adenoma detection, particularly in the proximal colon.

PMID: unknown
Title: Non-Aquaporin Water Channels.
Year: 2023
Abstract: Water transport through membrane is so intricate that there are still some debates. AQPs are entirely accepted to allow water transmembrane movement depending on osmotic gradient. Cotransporters and uniporters, however, are also concerned in water homeostasis. UT-B has a single-channel water permeability that is similar to AQP1. CFTR was initially thought as a water channel but now not believed to transport water directly. By cotransporters, such as KCC4, NKCC1, SGLT1, GAT1, EAAT1, and MCT1, water is transported by water osmosis coupling with substrates, which explains how water is transported across the isolated small intestine. This chapter provides information about water transport mediated by other membrane proteins except AQPs.

PMID: unknown
Title: Measuring Human Water Needs.
Year: 2020
Abstract: Water connects the environment, culture, and biology, yet only recently has it emerged as a major focus for research in human biology. To facilitate such research, we describe methods to measure biological, environmental, and perceptual indicators of human water needs. This toolkit provides an overview of methods for assessing different dimensions of human water need, both well-established and newly-developed. These include: (a) markers of hydration (eg, urine specific gravity, doubly labeled water) important for measuring the impacts of water need on human biological functioning; (b) methods for measuring water quality (eg, digital colorimeter, membrane filtration) essential for understanding the health risks associated with exposure to microbiological, organic, metal, inorganic nonmental, and other contaminants; and (c) assessments of household water insecurity status that track aspects of unmet water needs (eg, inadequate water service, unaffordability, and experiences of water insecurity) that are directly relevant to human health and biology. Together, these methods can advance new research about the role of water in human biology and health, including the ways that insufficient, unsafe, or insecure water produces negative biological and health outcomes.

PMID: unknown
Title: Water-transporting proteins.
Year: 2010
Abstract: Transport through lipids and aquaporins is osmotic and entirely driven by the difference in osmotic pressure. Water transport in cotransporters and uniporters is different: Water can be cotransported, energized by coupling to the substrate flux by a mechanism closely associated with protein. In the K(+)/Cl(-) and the Na(+)/K(+)/2Cl(-) cotransporters, water is entirely cotransported, while water transport in glucose uniporters and Na(+)-coupled transporters of nutrients and neurotransmitters takes place by both osmosis and cotransport. The molecular mechanism behind cotransport of water is not clear. It is associated with the substrate movements in aqueous pathways within the protein; a conventional unstirred layer mechanism can be ruled out, due to high rates of diffusion in the cytoplasm. The physiological roles of the various modes of water transport are reviewed in relation to epithelial transport. Epithelial water transport is energized by the movements of ions, but how the coupling takes place is uncertain. All epithelia can transport water uphill against an osmotic gradient, which is hard to explain by simple osmosis. Furthermore, genetic removal of aquaporins has not given support to osmosis as the exclusive mode of transport. Water cotransport can explain the coupling between ion and water transport, a major fraction of transepithelial water transport and uphill water transport. Aquaporins enhance water transport by utilizing osmotic gradients and cause the osmolarity of the transportate to approach isotonicity.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

