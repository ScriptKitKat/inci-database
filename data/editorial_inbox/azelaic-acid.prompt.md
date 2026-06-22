# Editorial prompt for: AZELAIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `azelaic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: AZELAIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: The versatility of azelaic acid in dermatology.
Year: 2022
Abstract: Azelaic acid has numerous pharmacological uses in dermatology. Its anti-inflammatory and anti-oxidant properties are thought to correlate with its efficacy in papulopustular rosacea and acne vulgaris, amongst other cutaneous conditions. We conducted a review of the literature on the use of azelaic acid in dermatology using key terms 'acne', 'azelaic acid', 'dermatology', 'melasma', 'rosacea', searching databases such as MEDLINE, EMBASE and PubMed. Only articles in English were chosen. The level of evidence was evaluated and selected accordingly listing the studies with the highest level of evidence first using the Oxford Center of Evidence-Based Medicine 2011 guidance.This review found the strongest evidence supporting the use of azelaic acid in rosacea, followed by its use off-label in melasma followed by acne vulgaris. Weaker evidence is currently available to support the use of azelaic acid in several other conditions such as hidradenitis suppurativa, keratosis pilaris and male androgenic alopecia.Azelaic acid, as a monotherapy or in combination, could be an effective first-line or alternative treatment, which is well-tolerated and safe for a range of dermatological conditions.

PMID: unknown
Title: Guidelines of care for the management of acne vulgaris.
Year: 2024
Abstract: Acne vulgaris commonly affects adults, adolescents, and preadolescents aged 9 years or older. The objective of this study was to provide evidence-based recommendations for the management of acne. A work group conducted a systematic review and applied the Grading of Recommendations, Assessment, Development, and Evaluation approach for assessing the certainty of evidence and formulating and grading recommendations. This guideline presents 18 evidence-based recommendations and 5 good practice statements. Strong recommendations are made for benzoyl peroxide, topical retinoids, topical antibiotics, and oral doxycycline. Oral isotretinoin is strongly recommended for acne that is severe, causing psychosocial burden or scarring, or failing standard oral or topical therapy. Conditional recommendations are made for topical clascoterone, salicylic acid, and azelaic acid, as well as for oral minocycline, sarecycline, combined oral contraceptive pills, and spironolactone. Combining topical therapies with multiple mechanisms of action, limiting systemic antibiotic use, combining systemic antibiotics with topical therapies, and adding intralesional corticosteroid injections for larger acne lesions are recommended as good practice statements. Analysis is based on the best available evidence at the time of the systematic review. These guidelines provide evidence-based recommendations for the management of acne vulgaris.

PMID: unknown
Title: Rosacea: Common Questions and Answers.
Year: 2024
Abstract: Rosacea is a chronic inflammatory skin disease of the central face, affecting 5% of the population. The exact etiology is unknown. A diagnosis is made based on the updated 2017 National Rosacea Society Expert Committee guidelines, including fixed erythema, phymatous changes of skin thickening due to sebaceous gland hyperplasia and fibrosis, papules, pustules, telangiectasia, and flushing. Delays in an accurate diagnosis and treatment may occur in skin of color due to difficulty visualizing erythema and telangiectasia. The daily use of sunscreen, moisturizers, and mild skin cleansers and avoidance of triggers are essential aspects of maintenance treatment. Effective topical treatment options include alpha-adrenergic receptor agonists for flushing and ivermectin, metronidazole, and azelaic acid for papules and pustules. Systemic treatments include nonselective beta blockers for flushing, low-dose doxycycline, and isotretinoin for papules and pustules. Rosacea can significantly affect a patient's emotional health and quality of life. A referral for care is recommended for fixed phymatous changes and ocular rosacea. (Am Fam Physician. 2024;109(6):533-542.

PMID: unknown
Title: Azelaic Acid: Mechanisms of Action and Clinical Applications.
Year: 2024
Abstract: AZA is a non-phenolic, saturated dicarboxylic acid with nine carbon atoms, naturally produced by the yeast Malassezia. It has diverse physiological activities, including antibacterial, anti-keratinizing, antimelanogenic, antioxidant and anti-inflammatory effects. AZA is widely used in dermatology and is FDA-approved for treating papulopustular rosacea. It also shows significant efficacy in acne vulgaris and melasma. This review summarizes the mechanisms of action and clinical applications of AZA, aiming to provide theoretical support for its clinical and cosmetic use and to facilitate further research.

PMID: unknown
Title: Skincare ingredients recommended by cosmetic dermatologists: A Delphi consensus study.
Year: 2025
Abstract: There is ambiguity regarding the topical cosmetic ingredients preferred for common skin complaints. To determine which topical ingredients are frequently recommended by cosmetic dermatologists for fine lines and wrinkles, acne, redness, dark spots, large pores, dry skin, and oily skin. Literature review to develop long list of ingredients. Reduced by expert panel to most salient ingredients. Two rounds of Delphi consensus survey with second expert panel of clinicians and teachers. Comparative literature review to summarize published evidence supporting each consensus ingredient. List of 318 ingredients reduced by a panel of 17 dermatologists to 83. Two Delphi rounds completed by 62 dermatologists at 43 centers. Consensus achieved for 23 ingredients, including the following: azelaic acid (acne, dark spots); benzoyl peroxide (acne, oily skin); glycolic acid (acne, dark spots); mineral sunscreen (fine lines and wrinkles, redness); niacinamide (redness, dark spots); retinoids (fine lines and wrinkles, acne, dark spots, large pores, oily skin); salicylic acid (acne, oily skin); vitamin C (fine lines and wrinkles, dark spots). Most consensus ingredients supported by level 1b or 2b evidence. Some ingredients based on expert opinion. Consensus exists among expert cosmetic dermatologists regarding ingredients most useful for common dermatologic concerns.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

