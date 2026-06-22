# Editorial prompt for: PHENOXYETHANOL

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `phenoxyethanol.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: PHENOXYETHANOL
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Safety review of phenoxyethanol when used as a preservative in cosmetics.
Year: 2019
Abstract: Phenoxyethanol, or 2-phenoxyethanol, has a large spectrum of antimicrobial activity and has been widely used as a preservative in cosmetic products for decades. It is effective against various Gram-negative and Gram-positive bacteria, as well as against yeasts, and has only a weak inhibitory effect on resident skin flora. According to the European Scientific Committee on Consumer Safety, phenoxyethanol is safe for all consumers - including children of all ages - when used as a preservative in cosmetic products at a maximum concentration of 1%. Adverse systemic effects have been observed in toxicological studies on animals but only when the levels of exposure were many magnitudes higher (around 200-fold higher) than those to which consumers are exposed when using phenoxyethanol-containing cosmetic products. Despite its widespread use in cosmetic products, phenoxyethanol is a rare sensitizer. It can be considered as one of the most well-tolerated preservatives used in cosmetic products.

PMID: unknown
Title: Consensus on Wound Antisepsis: Update 2018.
Year: 2018
Abstract: Wound antisepsis has undergone a renaissance due to the introduction of highly effective wound-compatible antimicrobial agents and the spread of multidrug-resistant organisms (MDROs). However, a strict indication must be set for the application of these agents. An infected or critically colonized wound must be treated antiseptically. In addition, systemic antibiotic therapy is required in case the infection spreads. If applied preventively, the Wounds-at-Risk Score allows an assessment of the risk for infection and thus appropriateness of the indication. The content of this updated consensus recommendation still largely consists of discussing properties of octenidine dihydrochloride (OCT), polihexanide, and iodophores. The evaluations of hypochlorite, taurolidine, and silver ions have been updated. For critically colonized and infected chronic wounds as well as for burns, polihexanide is classified as the active agent of choice. The combination 0.1% OCT/phenoxyethanol (PE) solution is suitable for acute, contaminated, and traumatic wounds, including MRSA-colonized wounds due to its deep action. For chronic wounds, preparations with 0.05% OCT are preferable. For bite, stab/puncture, and gunshot wounds, polyvinylpyrrolidone (PVP)-iodine is the first choice, while polihexanide and hypochlorite are superior to PVP-iodine for the treatment of contaminated acute and chronic wounds. For the decolonization of wounds colonized or infected with MDROs, the combination of OCT/PE is preferred. For peritoneal rinsing or rinsing of other cavities with a lack of drainage potential as well as the risk of central nervous system exposure, hypochlorite is the superior active agent. Silver-sulfadiazine is classified as dispensable, while dyes, organic mercury compounds, and hydrogen peroxide alone are classified as obsolete. As promising prospects, acetic acid, the combination of negative pressure wound therapy with the instillation of antiseptics (NPWTi), and cold atmospheric plasma are also subjects of this assessment.

PMID: unknown
Title: Stimulation of hair regrowth in an animal model of androgenic alopecia using 2-deoxy-D-ribose.
Year: 2024
Abstract: Androgenic alopecia (AGA) affects both men and women worldwide. New blood vessel formation can restore blood supply and stimulate the hair regrowth cycle. Recently, our group reported that 2-deoxy-D-ribose (2dDR) is 80%-90% as effective as VEGF in the stimulation of neovascularization in

PMID: unknown
Title: Shampoos.
Year: 2009
Abstract: Shampoos are used almost universally in developed countries to wash the hair on a daily basis. A number of known contact allergens are used as ingredients in shampoos, and contact allergy due to shampoos is a well known entity. Patch testing can be used to identify ingredients to which patients are allergic, after which the physician can help the patient to find a shampoo that is free of the ingredients to which they are allergic. The ingredients used in shampoos have not been systematically reviewed in recent years in the United States. We use a database of products sold at a major drug store to quantify the most frequent allergens used in shampoos. The allergens most commonly present, in order of prevalence are as follows: fragrance, cocamidopropyl betaine, methylchloroisothiazolinone/methylisothiazolinone, formaldehyde releasers, propylene glycol, vitamin E, parabens, benzophenones, iodopropynyl butylcarbamate, and methyldibromoglutaronitrile/phenoxyethanol.

PMID: unknown
Title: RIFM fragrance ingredient safety assessment, 2-phenoxyethanol, CAS Registry Number 122-99-6.
Year: 2019
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

