# Editorial prompt for: HYALURONIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `hyaluronic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: HYALURONIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Hyaluronic Acid: A Key Ingredient in the Therapy of Inflammation.
Year: 2021
Abstract: Hyaluronic acid (HA) is a natural polymer, produced endogenously by the human body, which has unique physicochemical and biological properties, exhibiting desirable biocompatibility and biodegradability. Therefore, it has been widely studied for possible applications in the area of inflammatory diseases. Although exogenous HA has been described as unable to restore or replace the properties and activities of endogenous HA, it can still provide satisfactory pain relief. This review aims to discuss the advances that have been achieved in the treatment of inflammatory diseases using hyaluronic acid as a key ingredient, essentially focusing on studies carried out between the years 2017 and 2021.

PMID: unknown
Title: Hyaluronic Acid Basics and Rheology.
Year: 2023
Abstract: Hyaluronic acid (HA) is the most common dermal filler in use. It improves wrinkles and volume loss not only by filling and volumizing but also by hydrating the injected area with its water affinity. It is a naturally occurring component of skin, and there is a negligible risk of immunologic or allergic reaction with injection. It is rapidly degraded by the injection of hyaluronidase, thus creating an ideal injectable material that is low risk and reversible. Its duration of effect may be longer than expected based on bioavailability of the HA product due to collagen synthesis or fibroblast stimulation.

PMID: unknown
Title: The Rheology and Physicochemical Characteristics of Hyaluronic Acid Fillers: Their Clinical Implications.
Year: 2022
Abstract: Hyaluronic acid (HA) fillers have become the most popular material for facial volume augmentation and wrinkle correction. Several filler brands are currently on the market all around the world and their features are extremely variable; for this reason, most users are unaware of their differences. The study of filler rheology has become a wellspring of knowledge, differentiating HA fillers, although these properties are not described thoroughly by the manufacturers. The authors of this review describe the more useful rheological properties that can help clinicians understand filler characteristics and the likely correlation of these features with clinical outcomes.

PMID: unknown
Title: Hyaluronic Acid Basics and Rheology.
Year: 2022
Abstract: Hyaluronic acid (HA) is the most common dermal filler in use. It improves wrinkles and volume loss not only by filling and volumizing but also by hydrating the injected area with its water affinity. It is a naturally occurring component of skin, and there is a negligible risk of immunologic or allergic reaction with injection. It is rapidly degraded by the injection of hyaluronidase, thus creating an ideal injectable material that is low risk and reversible. Its duration of effect may be longer than expected based on bioavailability of the HA product due to collagen synthesis or fibroblast stimulation.

PMID: unknown
Title: [Hyaluronic acid].
Year: 2008
Abstract: Hyaluronic Acid (HA) is now a leader product in esthetic procedures for the treatment of wrinkles and volumes. The structure of HA, its metabolism, its physiological function are foremost breaking down then its use in aesthetic dermatology: steps of injection, possible side effects, benefits and downsides of the use of HA in aesthetic dermatology.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

