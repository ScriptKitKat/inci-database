# Editorial prompt for: NIACINAMIDE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `niacinamide.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: NIACINAMIDE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Niacinamide: A B vitamin that improves aging facial skin appearance.
Year: 2005
Abstract: In multiple chronic clinical studies, topical niacinamide (vitamin B3) has been observed to be well tolerated by skin and to provide a broad array of improvements in the appearance of aging facial skin (eg, reduction in the appearance of hyperpigmentated spots and red blotchiness). To clinically determine the effect of topical niacinamide on additional skin appearance and property end points (wrinkles, yellowing, and elasticity). Female white subjects (N = 50) with clinical signs of facial photoaging (fine lines and wrinkles, poor texture, and hyperpigmented spots) applied 5% niacinamide to half of the face and its vehicle control to the other half twice daily for 12 weeks (double blind, left-right randomized). Facial images and instrumental measures were obtained at baseline and at 4-week intervals. Analyses of the data revealed a variety of significant skin appearance improvement effects for topical niacinamide: reductions in fine lines and wrinkles, hyperpigmented spots, red blotchiness, and skin sallowness (yellowing). In addition, elasticity (as measured via cutometry) was improved. Corresponding mechanistic information is presented. In addition to previously observed benefits for topical niacinamide, additional effects were identified (improved appearance of skin wrinkles and yellowing and improved elasticity).

PMID: unknown
Title: Nicotinic acid/niacinamide and the skin.
Year: 2004
Abstract: Nicotinic acid (also generally known as niacin) and niacinamide (also known as nicotinamide) are similarly effective as a vitamin because they can be converted into each other within the organism. The blanket term vitamin B(3) is used for both. Niacinamide is a component of important coenzymes involved in hydrogen transfer. Here, the two codehydrogenases, nicotinamide adenine dinucleotide (NAD) and nicotinamide adenine dinucleotide phosphate (NADP) are of central importance. Topical application of niacinamide has a stabilizing effect on epidermal barrier function, seen as a reduction in transepidermal water loss and an improvement in the moisture content of the horny layer. Niacinamide leads to an increase in protein synthesis (e.g. keratin), has a stimulating effect on ceramide synthesis, speeds up the differentiation of keratinocytes, and raises intracellular NADP levels. In ageing skin, topical application of niacinamide improves the surface structure, smoothes out wrinkles and inhibits photocarcinogenesis. It is possible to demonstrate anti-inflammatory effects in acne, rosacea and nitrogen mustard-induced irritation. Because of its verifiable beneficial effects, niacinamide would be a suitable component in cosmetic products for use in disorders of epidermal barrier function, for ageing skin, for improving pigmentary disorders and for use on skin prone to acne.

PMID: unknown
Title: Niacinamide - mechanisms of action and its topical use in dermatology.
Year: 2014
Abstract: Niacinamide, an amide of vitamin B3 (niacin), is a hydrophilic endogenous substance. Its effects after epicutaneous application have long been described in the literature. Given a sufficient bioavailability, niacinamide has antipruritic, antimicrobial, vasoactive, photo-protective, sebostatic and lightening effects depending on its concentration. Within a complex metabolic system niacinamide controls the NFκB-mediated transcription of signalling molecules by inhibiting the nuclear poly (ADP-ribose) polymerase-1 (PARP-1). Niacinamide is a well-tolerated and safe substance often used in cosmetics. Clinical data for its therapeutic use in various dermatoses can increasingly be found in the literature. Although the existing data are not sufficient for a scientifically founded evaluation, it can be stated that the use of niacinamide in galenic preparations for epicutaneous application offers most interesting prospects.

PMID: unknown
Title: Cosmeceutical Aptitudes of Niacinamide: A Review.
Year: 2021
Abstract: The prevalence and scope of dermatological illness differ from region to region. Based upon type and severity, the conditions may vary from superficial to deep systemic skin infections. Niacinamide, an amide analog of vitamin B3 which was conventionally utilized as a food supplement, is now explored for the management of skin disorders. Being a powerhouse on its own, it is not stored inside the body naturally and has to be acquired from external sources. Areas Covered: This review is an attempt to disclose the physiology, pharmacology, and highlight the dermatological potentials of niacinamide, discussing its pharmacological mechanisms, varied commercially available treatments, and novel approaches, i.e., in research and patented formulations. Niacinamide has been verified in treating almost every skin disorder, viz. aging, hyperpigmentation, acne, psoriasis, pruritus, dermatitis, fungal infections, epidermal melasma, non-melanoma skin cancer, etc. It has been reported to possess numerous properties, for instance, anti-inflammatory, antimicrobial, antioxidant, antipruritic, and anticancer, which makes it an ideal ingredient for varied dermal therapies. Long term use of niacinamide, regardless of the skin type, paves the way for new skin cells, making skin healthier, brighter, and hydrated. Niacinamide possesses a variety of positive characteristics in the field of dermatology. Novel approaches are warranted over current treatments which could bypass the above shortcomings and form an effective and stable system. Hence, niacinamide has the potential to become an individual and a productive component with wide future scope.

PMID: unknown
Title: Niacinamide: a review on dermal delivery strategies and clinical evidence.
Year: 2024
Abstract: Niacinamide, an active form of vitamin B3, is recognised for its significant dermal benefits including skin brightening, anti-ageing properties and the protection of the skin barrier. Its widespread incorporation into cosmetic products, ranging from cleansers to serums, is attributed to its safety profile and proven efficacy. Recently, topical niacinamide has also been explored for other pharmaceutical applications, including skin cancers. Therefore, a fundamental understanding of the skin permeation behaviour of niacinamide becomes crucial for formulation design. Given the paucity of a comprehensive review on this aspect, we provide insights into the mechanisms of action of topically applied niacinamide and share the current strategies used to enhance its skin permeation. This review also consolidates clinical evidence of topical niacinamide for its cosmeceutical uses and as treatment for some skin disorders, including dermatitis, acne vulgaris and actinic keratosis. We also emphasise the current exploration and perspectives on the delivery designs of topical niacinamide, highlighting the potential development of formulations focused on enhancing skin permeation, particularly for clinical benefits.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

