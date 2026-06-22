# Editorial prompt for: ZINC OXIDE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `zinc-oxide.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: ZINC OXIDE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Zinc oxide nanoparticles: future therapy for cerebral ischemia.
Year: 2020
Abstract: 

PMID: unknown
Title: A review: zinc oxide nanoparticles - friends or enemies?
Year: 2022
Abstract: Modern nanotechnology allows obtaining zinc oxide nanomaterials with unique properties that let its use in a wide range of commercial applications. Direct contact with these particles as well as their release into the environment is almost inevitable. This review aims to consider whether the toxicity of zinc oxide nanoparticles found in numerous test models is a real threat to humans and plants. Emerging reports indicated both the risks and benefits associated with the use of zinc oxide nanoparticles in a manner dependent on the concentration and a method of synthesis, as well as the tested object. The amounts needed to achieve the antibacterial activity of ZnO-NPs, and the reported amounts of these nanoparticles in consumer products are sufficient to have a negative impact on living organisms. The most sensitive to their action are human cells, and the mechanism of cytotoxicity is mainly associated with the formation of oxidative stress caused by the action of zinc ions. ZnO-NPs in small concentration can have positive affect to plants, but it poses a threat to more sensitive ones.

PMID: unknown
Title: Alternatives to zinc oxide in pig production.
Year: 2023
Abstract: Zinc oxide (ZnO) has been applied for many years in the production of pigs to reduce the number of diarrhoea in weaned piglets. In June 2022, the European Union banned the use of zinc oxide (ZnO) in pig feed. According to scientific reports, the may reason was the accumulation of this microelement in the environment of pig production. It has been shown that frequent application of ZnO can lead to increased antibiotic resistance in pathogenic swine microflora. The main alternatives to ZnO are probiotics, prebiotics, organic acids, essential oils, and liquid feeding systems. Alternatives to ZnO can be successfully used in pig production to reduce the number of diarrhoea among piglets during the postweaning period. Additional reports indicated that bacteriophage supplementation has a positive effect on the health of pigs. The article provides an overview of current ZnO substitutes that can be used in pig farming.

PMID: unknown
Title: Safety assessment of silica and zinc oxide nanoparticles.
Year: 2014
Abstract: 

PMID: unknown
Title: Zinc oxide and zinc oxide-based nanostructures: biogenic and phytogenic synthesis, properties and applications.
Year: 2021
Abstract: Zinc oxide nanoparticles (ZnO NPs) are considered as very significant and essential material due to its multifunctional properties, stability, low cost and wide usage. Many green and biogenic approaches for ZnO NPs synthesis have been reported using various sources such as plants and microorganisms. Plants contain biomolecules that can act as capping, oxidizing and reducing agents that increase the rate of reaction and stabilizes the NPs. This review emphasizes and compiles different types of plants and parts of plant used for the synthesis of ZnO and its potential applications at one place. The influence of biogenic and phytogenic synthesized ZnO on its properties and possible mechanisms for its fabrication has been discussed. This review also highlights the potential applications and future prospects of phytogenic synthesized ZnO in the field of energy production and storage, sun light harvesting, environmental remediation, and biological applications.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

