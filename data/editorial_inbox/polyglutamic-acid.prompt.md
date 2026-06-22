# Editorial prompt for: POLYGLUTAMIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `polyglutamic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: POLYGLUTAMIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Polyglutamylation of microtubules drives neuronal remodeling.
Year: 2025
Abstract: Developmental remodeling shapes neural circuits via activity-dependent pruning of synapses and axons. Regulation of the cytoskeleton is critical for this process, as microtubule loss via enzymatic severing is an early step of pruning across many circuits and species. However, how microtubule-severing enzymes, such as spastin, are activated in specific neuronal compartments remains unknown. Here, we reveal that polyglutamylation, a post-translational tubulin modification enriched in neurons, plays an instructive role in developmental remodeling by tagging microtubules for severing. Motor neuron-specific gene deletion of enzymes that add or remove tubulin polyglutamylation-TTLL glutamylases vs. CCP deglutamylases-accelerates or delays neuromuscular synapse remodeling in a neurotransmission-dependent manner. This mechanism is not specific to peripheral synapses but also operates in central circuits, e.g., the hippocampus. Thus, tubulin polyglutamylation acts as a cytoskeletal rheostat of remodeling that shapes neuronal morphology and connectivity.

PMID: unknown
Title: A Nature-Inspired Versatile Bio-Adhesive.
Year: 2023
Abstract: The application of most hydrogel bio-adhesives is greatly limited due to their high swelling, low underwater adhesion, and single function. Herein, a spatial multi-level physical-chemical and bio-inspired in-situ bonding strategy is proposed, to develop a multifunctional hydrogel bio-glue using polyglutamic acid (PGA), tyramine hydrochloride (TYR), and tannic acid (TA) as precursors and 4-(4,6-dimethoxytriazine-2-yl) -4-methylmorpholine hydrochloride(DMTMM) as condensation agent, which is used for tissue adhesion, hemostasis and repair. By introducing TYR and TA into the PGA chain, it is demonstrated that not only can the strong adhesion of bio-glue to the surface of various fresh tissues and wet materials be realized through the synergistic effect of spatial multi-level physical and chemical bonding, but also this glue can be endowed with the functions of anti-oxidation and hemostasis. The excellent performance of such bio-glue in the repair of the wound, liver, and cartilage is achieved, showing a great potential in clinical application for such bio-glue. This study will open up a brand-new avenue for the development of multifunctional hydrogel biological adhesive.

PMID: unknown
Title: Synthetic polyglutamic acid.
Year: 1948
Abstract: 

PMID: unknown
Title: Nano-Polymers as Cas9 Inhibitors.
Year: 2025
Abstract: Despite wide applications of CRISPR/Cas9 technology, effective approaches for CRISPR delivery with functional control are limited. In an attempt to develop a nanoscale CRSIPR/Cas9 delivery platform, we discovered that several biocompatible polymers, including polymalic acid (PMLA), polyglutamic acid (PGA), and polyaspartic acid (PLD), when conjugated with a trileucine (LLL) moiety, can effectively inhibit Cas9 nuclease function. The Cas9 inhibition by those polymers is dose-dependent, with varying efficiency to achieve 100% inhibition. Further biophysical studies revealed that PMLA-LLL directly binds the Cas9 protein, resulting in a substantial decrease in Cas9/sgRNA binding affinity. Transmission electron microscopy and molecular docking were performed to provide a possible binding mechanism for PMLA-LLL to interact with Cas9. This work identified a new class of Cas9 inhibitor in nano-polymer form. These biodegradable polymers may serve as novel Cas9 delivery vehicles with a potential to enhance the precision of Cas9-mediated gene editing.

PMID: unknown
Title: Editorial: Monitoring methotrexate polyglutamates in Crohn's disease.
Year: 2024
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

