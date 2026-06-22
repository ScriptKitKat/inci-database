# Editorial prompt for: TRANEXAMIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `tranexamic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: TRANEXAMIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: THE USE OF TRANEXAMIC ACID IN DERMATOLOGY.
Year: 2023
Abstract: Tranexamic acid is a synthetic derivative of the amino acid lysine, an antifibrinolytic that is primarily used to reduce bleeding in surgery, trauma, and dental procedures. Its anti-inflammatory and anti-angiogenic properties, as well as its ability to suppress melanogenesis have enabled it to be used in dermatology in the treatment of skin conditions such as melasma, acne, post-inflammatory hyperpigmentation, rosacea and angioedema. Tranexamic acid can be used by various routes of administration including oral, topical and intradermal injection, and in combination with other treatment methods. This review article presents evidence for the effectiveness of tranexamic acid in the treatment of various skin disorders.

PMID: unknown
Title: Tranexamic acid: Beyond antifibrinolysis.
Year: 2022
Abstract: Tranexamic acid (TXA) is a popular antifibrinolytic drug widely used in hemorrhagic trauma patients and cardiovascular, orthopedic, and gynecological surgical patients. TXA binds plasminogen and prevents its maturation to the fibrinolytic enzyme plasmin. A number of studies have demonstrated the broad life-saving effects of TXA in trauma, superior to those of other antifibrinolytic agents. Besides preventing fibrinolysis and blood loss, TXA has been reported to suppress posttraumatic inflammation and edema. Although the efficiency of TXA transcends simple inhibition of fibrinolysis, little is known about its mechanisms of action besides the suppression of plasmin maturation. Understanding the broader effects of TXA at the cell, organ, and organism levels are required to elucidate its potential mechanisms of action transcending antifibrinolytic activity. In this article, we provide a brief review of the current clinical use of TXA and then focus on the effects of TXA beyond antifibrinolytics such as its anti-inflammatory activity, protection of the endothelial and epithelial monolayers, stimulation of mitochondrial respiration, and suppression of melanogenesis.

PMID: unknown
Title: Inhaled Tranexamic Acid as an Alternative for Hemoptysis Treatment.
Year: 2016
Abstract: 

PMID: unknown
Title: Tranexamic acid in total knee arthroplasty.
Year: 2023
Abstract: 

PMID: unknown
Title: Preventing neuraxial administration of tranexamic acid.
Year: 2023
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

