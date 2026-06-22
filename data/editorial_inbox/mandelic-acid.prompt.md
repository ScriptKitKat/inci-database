# Editorial prompt for: MANDELIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `mandelic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: MANDELIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: [CURABLE HYPERTENSION].
Year: 1964
Abstract: 

PMID: unknown
Title: Arylacetonitrilases: Potential Biocatalysts for Green Chemistry.
Year: 2024
Abstract: Nitrilases are the enzymes that catalyze the hydrolysis of nitriles to corresponding carboxylic acid and ammonia. They are broadly categorized into aromatic, aliphatic, and arylacetonitrilases based on their substrate specificity. Most of the studies pertaining to these enzymes in the literature have focused on aromatic and aliphatic nitrilases. However, arylacetonitrilases have attracted the attention of academia and industry in the last several years due to their aryl specificity and enantioselectivity. They have emerged as interesting biocatalytic tools in green chemistry to synthesize useful aryl acids such as mandelic acid and derivatives of phenylacetic acid. The aim of the present review is to collate information on the arylacetonitrilases and their catalytic properties including enantioselectivity and potential applications in organic synthesis.

PMID: unknown
Title: Bacterial mandelic acid degradation pathway and its application in biotechnology.
Year: 2022
Abstract: Mandelic acid and its derivatives are an important class of chemical synthetic blocks, which is widely used in drug synthesis and stereochemistry research. In nature, mandelic acid degradation pathway has been widely identified and analysed as a representative pathway of aromatic compounds degradation. The most studied mandelic acid degradation pathway from Pseudomonas putida consists of mandelate racemase, S-mandelate dehydrogenase, benzoylformate decarboxylase, benzaldehyde dehydrogenase and downstream benzoic acid degradation pathways. Because of the ability to catalyse various reactions of aromatic substrates, pathway enzymes have been widely used in biocatalysis, kinetic resolution, chiral compounds synthesis or construction of new metabolic pathways. In this paper, the physiological significance and the existing range of the mandelic acid degradation pathway were introduced first. Then each of the enzymes in the pathway is reviewed one by one, including the researches on enzymatic properties and the applications in biotechnology as well as efforts that have been made to modify the substrate specificity or improving catalytic activity by enzyme engineering to adapt different applications. The composition of the important metabolic pathway of bacterial mandelic acid degradation pathway as well as the researches and applications of pathway enzymes is summarized in this review for the first time.

PMID: unknown
Title: [STYRENES].
Year: 1963
Abstract: 

PMID: unknown
Title: Green synthesis aspects of (R)-(-)-mandelic acid; a potent pharmaceutically active agent and its future prospects.
Year: 2023
Abstract: (R)-(-)-mandelic acid is an important carboxylic acid known for its numerous potential applications in the pharmaceutical industry as it is an ideal starting material for the synthesis of antibiotics, antiobesity drugs and antitumor agents. In past few decades, the synthesis of (R)-(-)-mandelic acid has been undertaken mainly through the chemical route. However, chemical synthesis of optically pure (R)-(-)-mandelic acid is difficult to achieve at an industrial scale. Therefore, its microbe mediated production has gained considerable attention as it exhibits many merits over the chemical approaches. The present review focuses on various biotechnological strategies for the production of (R)-(-)-mandelic acid through microbial biotransformation and enzymatic catalysis; in particular, an analysis and comparison of the synthetic methods and different enzymes. The wild type as well as recombinant microbial strains for the production of (R)-(-)-mandelic acid have been elucidated. In addition, different microbial strategies used for maximum bioconversion of mandelonitrile into (R)-(-)-mandelic acid are discussed in detail with regard to higher substrate tolerance and maximum bioconversion.HighlightsMandelonitrile, mandelamide and o-chloromandelonitrile can be used as substrates to produce (R)-(-)-mandelic acid by enzymes.Three enzymes (nitrilase, nitrile hydratase and amidase) are systematically introduced for production of (R)-(-)-mandelic acid.Microbial transformation is able to produce optically pure (R)-(-)-mandelic acid with 100% productive yield.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

