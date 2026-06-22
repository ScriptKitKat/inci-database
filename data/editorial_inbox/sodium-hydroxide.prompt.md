# Editorial prompt for: SODIUM HYDROXIDE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `sodium-hydroxide.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: SODIUM HYDROXIDE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Preparation of PCR-quality mouse genomic DNA with hot sodium hydroxide and tris (HotSHOT).
Year: 2000
Abstract: 

PMID: unknown
Title: Sulfoethylation of polysaccharides-A comparative study.
Year: 2020
Abstract: The heterogeneous sulfoethylation of cellulose, xylan, α-1,3-glucan, glucomannan, pullulan, curdlan, galactoglucomannan, and agarose was studied using sodium vinylsulfonate (NaVS) as reagent in presence of sodium hydroxide and iso-propanol (i-PrOH) as slurry medium. The influence of the concentration of polymer, water, and NaOH (solid or aqueous solution) on the degree of substitution (DS) was investigated. The sulfoethylation rendered the polysaccharides studied water-soluble. Sulfoethylation of heteropolysaccharides yielded products with higher DS compared to the conversion of homopolysaccharides. Structure characterization was carried out by means of

PMID: unknown
Title: Untangling the threads of cellulose mercerization.
Year: 2022
Abstract: Naturally occurring plant cellulose, our most abundant renewable resource, consists of fibers of long polymer chains that are tightly packed in parallel arrays in either of two crystal phases collectively referred to as cellulose I. During mercerization, a process that involves treatment with sodium hydroxide, cellulose goes through a conversion to another crystal form called cellulose II, within which every other chain has remarkably changed direction. We designed a neutron diffraction experiment with deuterium labelling in order to understand how this change of cellulose chain direction is possible. Here we show that during mercerization of bacterial cellulose, chains fold back on themselves in a zigzag pattern to form crystalline anti-parallel domains. This result provides a molecular level understanding of one of the most widely used industrial processes for improving cellulosic materials.

PMID: unknown
Title: Sodium Hydroxide versus Phenol Chemical Matrixectomy.
Year: 2025
Abstract: Chemical matrixectomy (CM) is a common procedure to correct painful and ingrown toenails. At our institution, CMs are often performed with either sodium hydroxide (NaOH) or phenol as the chemical agent for germinal nail matrix destruction. The primary aim of this study was to evaluate the recurrence and reoperation rates for this procedure using different chemical agents. The medical records of 192 patients during a 2-year period were reviewed. All of the CMs were performed in a standard fashion by three podiatric physicians. Among phenol partial nail avulsions, 46 nail border removals were performed. Among NaOH partial nail avulsions, 258 nail borders were treated. Mean follow-up was 93 days (median, 17 days). Among partial nail avulsions, the mean reoperation rate per border for CM with phenol was 6.5%. In comparison, the reoperation rate for CM with NaOH was 7.8% (P = .89), indicating that there is no statistically significant difference in reoperation rates between these two chemicals. The mean recurrence of painful nail edge rate per border for CM with phenol was 10.9%. In contrast, with NaOH this rate was 8.1% (P = .58), indicating that there was no statistically significant difference in the rate of development of recurrent painful nail borders between the two procedures. This retrospective medical record review demonstrated little difference between these chemicals in their reoperation and recurrence rates.

PMID: unknown
Title: COLLAGENS--PHYLOGENETIC CONSIDERATIONS.
Year: 1965
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

