# Editorial prompt for: TITANIUM DIOXIDE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `titanium-dioxide.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: TITANIUM DIOXIDE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Photoprotection beyond ultraviolet radiation: A review of tinted sunscreens.
Year: 2021
Abstract: Ultraviolet radiation and visible light both have biologic effects on the skin. Visible light can induce erythema in light-skinned individuals and pigmentation in dark-skinned individuals. Broad-spectrum sunscreens protect against ultraviolet radiation but do not adequately protect against visible light. For a sunscreen to protect against visible light, it must be visible on the skin. Inorganic filters (also known as mineral filters), namely, zinc oxide and titanium dioxide, are used in the form of nanoparticles in sunscreens to minimize the chalky and white appearance on the skin; as such, they do not protect against visible light. Tinted sunscreens use different formulations and concentrations of iron oxides and pigmentary titanium dioxide to provide protection against visible light. Many shades of tinted sunscreens are available by combining different amounts of iron oxides and pigmentary titanium dioxide to cater to all skin phototypes. Therefore, tinted sunscreens are beneficial for patients with visible light-induced photodermatoses and those with hyperpigmentation disorders such as melasma and postinflammatory hyperpigmentation.

PMID: unknown
Title: Titanium dioxide.
Year: 1989
Abstract: 

PMID: unknown
Title: Titanium Dioxide: Structure, Impact, and Toxicity.
Year: 2022
Abstract: Titanium dioxide, first manufactured a century ago, is significant in industry due to its chemical inertness, low cost, and availability. The white mineral has a wide range of applications in photocatalysis, in the pharmaceutical industry, and in food processing sectors. Its practical uses stem from its dual feature to act as both a semiconductor and light scatterer. Optical performance is therefore of relevance in understanding how titanium dioxide impacts these industries. Recent breakthroughs are summarised herein, focusing on whether restructuring the surface properties of titanium dioxide either enhances or inhibits its reactivity, depending on the required application. Its recent exposure as a potential carcinogen to humans has been linked to controversies around titanium dioxide's toxicity; this is discussed by illustrating discrepancies between experimental protocols of toxicity assays and their results. In all, it is important to review the latest achievements in fast-growing industries where titanium dioxide prevails, while keeping in mind insights into its disputed toxicity.

PMID: unknown
Title: Introduction: titanium dioxide (TiO2) nanomaterials.
Year: 2014
Abstract: 

PMID: unknown
Title: Hepatotoxicity of titanium dioxide nanoparticles.
Year: 2025
Abstract: The food additive E171 (titanium dioxide, TiO

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

