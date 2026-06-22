# Editorial prompt for: SQUALANE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `squalane.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: SQUALANE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: The Role of Moisturizer Containing Anti-inflammatory on Skin Hydration in Mild-Moderate Atopic Dermatitis Patients.
Year: 2024
Abstract: Atopic dermatitis (AD) is a chronic, inflammatory skin condition characterized by eczema lesions and dry, itchy skin. Recent guidelines for the management of AD emphasize the importance of using moisturizers in the management of AD. This study is a double-blind clinical trial to determine the effectiveness of moisturizers containing anti-inflammatory ingredients compared with moisturizers without anti-inflammatory ingredients for skin hydration in mild to moderate adult AD patients for 14 days at the Dermatology and Venereology Outpatient Clinic at Dr. Soetomo General Academic Hospital. There was a significant difference (

PMID: unknown
Title: Biological importance and applications of squalene and squalane.
Year: 2012
Abstract: Squalene is a polyunsaturated hydrocarbon with a formula of C₃₀H₅₀. Squalene can be found in certain fish oils, especially shark liver oil, in high amounts and some vegetable oils in relatively smaller amounts. Human sebum also contains 13% squalene as one of its major constituents. Squalane is a saturated derivative of squalene and also found in these sources. Interest in squalene has been raised after its characterization in shark liver oil which is used as a traditional medicine for decades. Several studies exhibited results that prove certain bioactivities for squalene and squalane. Up to date, anticancer, antioxidant, drug carrier, detoxifier, skin hydrating, and emollient activities of these substances have been reported both in animal models and in vitro environments. According to promising results from recent studies, squalene and squalane are considered important substances in practical and clinical uses with a huge potential in nutraceutical and pharmaceutical industries.

PMID: unknown
Title: Squalane and Squalene.
Year: 2023
Abstract: The Expert Panel for Cosmetic Ingredient Safety reviewed newly available studies since their original assessment in 1982, along with updated information regarding product types and concentrations of use, and confirmed that Squalane and Squalene are safe as cosmetic ingredients in the practices of use and concentration as described in this report.

PMID: unknown
Title: Squalene and squalane emulsions as adjuvants.
Year: 1999
Abstract: Microfluidized squalene or squalane emulsions are efficient adjuvants, eliciting both humoral and cellular immune responses. Microfluidization stabilizes the emulsions and allows sterilization by terminal filtration. The emulsions are stable for years at ambient temperature and can be frozen. Antigens are added after emulsification so that conformational epitopes are not lost by denaturation and to facilitate manufacture. A Pluronic block copolymer can be added to the squalane or squalene emulsion. Soluble antigens administered in such emulsions generate cytotoxic T lymphocytes able to lyse target cells expressing the antigen in a genetically restricted fashion. Optionally a relatively nontoxic analog of muramyl dipeptide (MDP) or another immunomodulator can be added; however, the dose of MDP must be restricted to avoid systemic side effects in humans. Squalene or squalane emulsions without copolymers or MDP have very little toxicity and elicit potent antibody responses to several antigens in nonhuman primates. They could be used to improve a wide range of vaccines. Squalene or squalane emulsions have been administered in human cancer vaccines, with mild side effects and evidence of efficacy, in terms of both immune responses and antitumor activity.

PMID: unknown
Title: Adjuvants and immune enhancement.
Year: 1994
Abstract: Adjuvants increase cell-mediated and humoral immune responses to specific antigens. Used with recombinant viral antigens, they can elicit the production of T lymphocytes that lyse target cells, expressing the antigen in a genetically restricted fashion. Adjuvants can augment the production of interferon-gamma, thereby favoring the production of protective antibody isotopes, such as immunoglobulin G2a in the mouse. Modern adjuvants display the efficacy of Freund's complete adjuvant without its side effects. One such adjuvant is Syntex adjuvant formulation, a synthetic analogue of muramyl dipeptide in a microfluidized squalane/squalene-in-water emulsion. Monophosphoryl lipid A in a similar lipid emulsion is also effective. Immune-stimulating complexes of saponin and antigens elicit potent cell-mediated and humoral responses. A purified saponin component has adjuvant activity with reduced side effects; liposomes also can have adjuvant activity. Administering antigens in adjuvants can overcome low responsiveness in very young and old experimental animals and in those that are genetically low responders. Adjuvants are likely components of a new generation of recombinant and subunit vaccines.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

