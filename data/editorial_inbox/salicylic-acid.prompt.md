# Editorial prompt for: SALICYLIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `salicylic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: SALICYLIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Salicylic Acid Steers the Growth-Immunity Tradeoff.
Year: 2020
Abstract: Plants possess an effective immune system to combat most microbial attackers. The activation of immune responses to biotrophic pathogens requires the hormone salicylic acid (SA). Accumulation of SA triggers a plethora of immune responses (like massive transcriptional reprogramming, cell wall strengthening, and production of secondary metabolites and antimicrobial proteins). A tradeoff of strong immune responses is the active suppression of plant growth and development. The tradeoff also works the opposite way, where active growth and developmental processes suppress SA production and immune responses. Here, we review research on the role of SA in the growth-immunity tradeoff and examples of how the tradeoff can be bypassed. This knowledge will be instrumental in resistance breeding of crops with optimal growth and effective immunity.

PMID: unknown
Title: Salicylic Acid: Biosynthesis and Signaling.
Year: 2021
Abstract: Salicylic acid (SA) is an essential plant defense hormone that promotes immunity against biotrophic and semibiotrophic pathogens. It plays crucial roles in basal defense and the amplification of local immune responses, as well as the establishment of systemic acquired resistance. During the past three decades, immense progress has been made in understanding the biosynthesis, homeostasis, perception, and functions of SA. This review summarizes the current knowledge regarding SA in plant immunity and other biological processes. We highlight recent breakthroughs that substantially advanced our understanding of how SA is biosynthesized from isochorismate, how it is perceived, and how SA receptors regulate different aspects of plant immunity. Some key questions in SA biosynthesis and signaling, such as how SA is produced via another intermediate, benzoic acid, and how SA affects the activities of its receptors in the transcriptional regulation of defense genes, remain to be addressed.

PMID: unknown
Title: Salicylic acid and jasmonic acid crosstalk in plant immunity.
Year: 2022
Abstract: The phytohormones salicylic acid (SA) and jasmonic acid (JA) are major players in plant immunity. Numerous studies have provided evidence that SA- and JA-mediated signaling interact with each other (SA-JA crosstalk) to orchestrate plant immune responses against pathogens. At the same time, SA-JA crosstalk is often exploited by pathogens to promote their virulence. In this review, we summarize our current knowledge of molecular mechanisms for and modulations of SA-JA crosstalk during pathogen infection.

PMID: unknown
Title: Salicylic Acid Signalling in Plants.
Year: 2020
Abstract: Ten articles published in the "Special Issue: Salicylic Acid Signalling in Plants" are summarized, in order to get a global picture about the mode of action of salicylic acid in plants, and about its interaction with other stress-signalling routes. Its ecological aspects and possible practical use are also discussed.

PMID: unknown
Title: A lncRNA fine-tunes salicylic acid biosynthesis to balance plant immunity and growth.
Year: 2022
Abstract: Constitutive activation of plant immunity is detrimental to plant growth and development. Here, we uncover the role of a long non-coding RNA (lncRNA) in fine-tuning the balance of plant immunity and growth. We find that a lncRNA termed salicylic acid biogenesis controller 1 (SABC1) suppresses immunity and promotes growth in healthy plants. SABC1 recruits the polycomb repressive complex 2 to its neighboring gene NAC3, which encodes a NAC transcription factor, to decrease NAC3 transcription via H3K27me3. NAC3 activates the transcription of isochorismate synthase 1 (ICS1), a key enzyme catalyzing salicylic acid (SA) biosynthesis. SABC1 thus represses SA production and plant immunity via decreasing NAC3 and ICS1 transcriptions. Upon pathogen infection, SABC1 is downregulated to derepress plant resistance to bacteria and viruses. Together, our findings reveal lncRNA SABC1 as a molecular switch in balancing plant defense and growth by modulating SA biosynthesis.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

