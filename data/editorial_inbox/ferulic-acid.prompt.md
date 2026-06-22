# Editorial prompt for: FERULIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `ferulic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: FERULIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Ferulic acid: A review of its pharmacology, pharmacokinetics and derivatives.
Year: 2021
Abstract: Ferulic acid, a kind of phenolic substance widely existing in plants, is an important active component of many traditional Chinese medicines. So far, it has been proved that ferulic acid has a variety of biological activities, especially in oxidative stress, inflammation, vascular endothelial injury, fibrosis, apoptosis and platelet aggregation. Many studies have shown that ferulic acid can inhibit PI3K/AKT pathway, the production of ROS and the activity of aldose reductase. The anti-inflammatory effect of ferulic acid is mainly related to the levels of PPAR γ, CAM and NF-κ B and p38 MAPK signaling pathways. Ferulic acid not only protects vascular endothelium by ERK1/2 and NO/ET-1 signal, but also plays an anti-fibrosis role by TGF-β/Smad and MMPs/TIMPs system. Moreover, ferulic acid has ant-apoptotic and anti-platelet effects. In addition to the pharmacological effects of ferulic acid, its pharmacokinetics and derivatives were also discussed in this paper. This review provides the latest summary of the latest research on ferulic acid.

PMID: unknown
Title: Antioxidant Properties of Ferulic Acid and Its Possible Application.
Year: 2018
Abstract: Ferulic acid has low toxicity and possesses many physiological functions (anti-inflammatory, antioxidant, antimicrobial activity, anticancer, and antidiabetic effect). It has been widely used in the pharmaceutical, food, and cosmetics industry. Ferulic acid is a free radical scavenger, but also an inhibitor of enzymes that catalyze free radical generation and an enhancer of scavenger enzyme activity. Ferulic acid has a protective role for the main skin structures: keratinocytes, fibroblasts, collagen, elastin. It inhibits melanogenesis, enhances angiogenesis, and accelerates wound healing. It is widely applied in skin care formulations as a photoprotective agent, delayer of skin photoaging processes, and brightening component. Nonetheless, its use is limited by its tendency to be rapidly oxidized.

PMID: unknown
Title: Ferulic acid stabilizes a solution of vitamins C and E and doubles its photoprotection of skin.
Year: 2005
Abstract: Ferulic acid is a potent ubiquitous plant antioxidant. Its incorporation into a topical solution of 15%l-ascorbic acid and 1%alpha-tocopherol improved chemical stability of the vitamins (C+E) and doubled photoprotection to solar-simulated irradiation of skin from 4-fold to approximately 8-fold as measured by both erythema and sunburn cell formation. Inhibition of apoptosis was associated with reduced induction of caspase-3 and caspase-7. This antioxidant formulation efficiently reduced thymine dimer formation. This combination of pure natural low molecular weight antioxidants provides meaningful synergistic protection against oxidative stress in skin and should be useful for protection against photoaging and skin cancer.

PMID: unknown
Title: Synergistic Modulation of Microglial Polarization by Acteoside and Ferulic Acid via Dual Targeting of Nrf2 and RORγt to Alleviate Depression-Associated Neuroinflammation.
Year: 2025
Abstract: Acteoside (ACT) and ferulic acid (FA), the principal bioactive constituents of Baihe Dihuang decoction (BDD), possess established anti-inflammatory and antidepressant properties, but their combined effect on microglial phenotype modulation remains unclear. Integrated multi-source data and machine learning identified ACT and FA as BDD's core components, mediating therapeutic effects via neurotransmitter regulation and inflammatory suppression. Co-administering ACT and FA at their BDD ratio replicated the parent formulation's anti-inflammatory and antidepressant effects. Both compounds stabilized Nrf2, with ACT exhibiting greater potency. Crucially, the ACT/FA combination shifted microglia from pro-inflammatory M1 to neuroprotective M2 phenotypes via dual activation of Nrf2 and RORγt pathways. Pharmacological inhibition or genetic knockdown of Nrf2 abolished these effects, confirming its central role. This dual mechanism concurrently rectifies neuroinflammation at its microglial source and impedes peripheral immune factor invasion, effectively restoring neuroimmune homeostasis in depression. These findings provide a mechanistic foundation for optimizing herbal-derived combinatorial therapies targeting microglial polarization.

PMID: unknown
Title: Ferulic acid attenuates Sarcopenia progression by inhibiting peroxisomal ACOX1.
Year: 2025
Abstract: Sarcopenia, an age-related syndrome characterized by progressive loss of skeletal muscle mass, strength, and function, is closely associated with oxidative stress, inflammation, and protein metabolism imbalance. Ferulic acid (FA), a natural antioxidant, may improve sarcopenia, but its mechanism remains unclear. Sarcopenia models were established using dexamethasone (Dex)-induced C2C12 cells and BALB/c mice. CCK-8 assay, DCFH-DA fluorescence probe, immunofluorescence, RT-qPCR, Western blot, ELISA, and enzyme activity assays were employed to evaluate FA's effects on cell viability, myotube differentiation, and inflammatory factors. The interaction protein ACOX1 were screened out and its expression and activity were analyzed. This study found that FA significantly restored Dex-induced decline in cell viability, reversed myotube atrophy (increased diameter), and reduced ubiquitin-proteasome system marker MuRF-1 expression. FA inhibited ACOX1 enzyme activity and protein expression, decreasing ROS production. In mice, FA intervention improved body weight, grip strength, and gastrocnemius cross-sectional area, suppressed E3 ubiquitin ligase MuRF-1 expression, promoted myotube differentiation marker MyoD, and reduced TNF-α/IL-6 levels through inhibiting ACOX1. In conclusion, FA mitigates peroxisomal oxidative stress by inhibiting ACOX1, reduces ROS accumulation and inflammation, and improves muscle protein metabolism imbalance, providing a novel mechanism for natural targeted therapy in sarcopenia.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

