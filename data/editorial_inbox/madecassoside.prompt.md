# Editorial prompt for: MADECASSOSIDE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `madecassoside.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: MADECASSOSIDE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Centella asiatica in cosmetology.
Year: 2013
Abstract: Centella asiatica known as Gotu Kola is a medicinal plant that has been used in folk medicine for hundreds of years as well as in scientifically oriented medicine. The active compounds include pentacyclic triterpenes, mainly asiaticoside, madecassoside, asiatic and madecassic acids. Centella asiatica is effective in improving treatment of small wounds, hypertrophic wounds as well as burns, psoriasis and scleroderma. The mechanism of action involves promoting fibroblast proliferation and increasing the synthesis of collagen and intracellular fibronectin content and also improvement of the tensile strength of newly formed skin as well as inhibiting the inflammatory phase of hypertrophic scars and keloids. Research results indicate that it can be used in the treatment of photoaging skin, cellulite and striae.

PMID: unknown
Title: Therapeutic properties and pharmacological activities of asiaticoside and madecassoside: A review.
Year: 2023
Abstract: Centella asiatica is an ethnomedicinal herbaceous species that grows abundantly in tropical and sub-tropical regions of China, India, South-Eastern Asia and Africa. It is a popular nutraceutical that is employed in various forms of clinical and cosmetic treatments. C. asiatica extracts are reported widely in Ayurvedic and Chinese traditional medicine to boost memory, prevent cognitive deficits and improve brain functions. The major bioactive constituents of C. asiatica are the pentacyclic triterpenoid glycosides, asiaticoside and madecassoside, and their corresponding aglycones, asiatic acid and madecassic acid. Asiaticoside and madecassoside have been identified as the marker compounds of C. asiatica in the Chinese Pharmacopoeia and these triterpene compounds offer a wide range of pharmacological properties, including neuroprotective, cardioprotective, hepatoprotective, wound healing, anti-inflammatory, anti-oxidant, anti-allergic, anti-depressant, anxiolytic, antifibrotic, antibacterial, anti-arthritic, anti-tumour and immunomodulatory activities. Asiaticoside and madecassoside are also used extensively in treating skin abnormalities, burn injuries, ischaemia, ulcers, asthma, lupus, psoriasis and scleroderma. Besides medicinal applications, these phytocompounds are considered cosmetically beneficial for their role in anti-ageing, skin hydration, collagen synthesis, UV protection and curing scars. Existing reports and experimental studies on these compounds between 2005 and 2022 have been selectively reviewed in this article to provide a comprehensive overview of the numerous therapeutic advantages of asiaticoside and madecassoside and their potential roles in the medical future.

PMID: unknown
Title: Pharmacological Effects of 
Year: 2021
Abstract: The medicinal herb

PMID: unknown
Title: Inhibitory Effect of Centella asiatica Extract on DNCB-Induced Atopic Dermatitis in HaCaT Cells and BALB/c Mice.
Year: 2020
Abstract: Atopic dermatitis (AD) is a chronic inflammatory skin disease caused mainly by immune dysregulation. This study explored the anti-inflammatory and immunomodulatory effects of the

PMID: unknown
Title: Topical Application of 
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

