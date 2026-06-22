# Editorial prompt for: BETA-GLUCAN

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `beta-glucan.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: BETA-GLUCAN
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: β-Glucan Reverses the Epigenetic State of LPS-Induced Immunological Tolerance.
Year: 2016
Abstract: Innate immune memory is the phenomenon whereby innate immune cells such as monocytes or macrophages undergo functional reprogramming after exposure to microbial components such as lipopolysaccharide (LPS). We apply an integrated epigenomic approach to characterize the molecular events involved in LPS-induced tolerance in a time-dependent manner. Mechanistically, LPS-treated monocytes fail to accumulate active histone marks at promoter and enhancers of genes in the lipid metabolism and phagocytic pathways. Transcriptional inactivity in response to a second LPS exposure in tolerized macrophages is accompanied by failure to deposit active histone marks at promoters of tolerized genes. In contrast, β-glucan partially reverses the LPS-induced tolerance in vitro. Importantly, ex vivo β-glucan treatment of monocytes from volunteers with experimental endotoxemia re-instates their capacity for cytokine production. Tolerance is reversed at the level of distal element histone modification and transcriptional reactivation of otherwise unresponsive genes. VIDEO ABSTRACT.

PMID: unknown
Title: β-Glucan Induces Protective Trained Immunity against Mycobacterium tuberculosis Infection: A Key Role for IL-1.
Year: 2020
Abstract: β-glucan is a potent inducer of epigenetic and functional reprogramming of innate immune cells, a process called "trained immunity," resulting in an enhanced host response against secondary infections. We investigate whether β-glucan exposure confers protection against pulmonary Mycobacterium tuberculosis (Mtb) infection. β-glucan induces trained immunity via histone modifications at gene promoters in human monocytes, which is accompanied by the enhanced production of proinflammatory cytokines upon secondary Mtb challenge and inhibition of Mtb growth. Mice treated with β-glucan are significantly protected against pulmonary Mtb infection, which is associated with the expansion of hematopoietic stem and progenitor cells in the bone marrow and increased myelopoiesis. The protective signature of β-glucan is mediated via IL-1 signaling, as β-glucan shows no protection in mice lacking a functional IL-1 receptor (IL1R

PMID: unknown
Title: β-Glucan phosphorylases in carbohydrate synthesis.
Year: 2021
Abstract: β-Glucan phosphorylases are carbohydrate-active enzymes that catalyze the reversible degradation of β-linked glucose polymers, with outstanding potential for the biocatalytic bottom-up synthesis of β-glucans as major bioactive compounds. Their preference for sugar phosphates (rather than nucleotide sugars) as donor substrates further underlines their significance for the carbohydrate industry. Presently, they are classified in the glycoside hydrolase families 94, 149, and 161 ( www.cazy.org ). Since the discovery of β-1,3-oligoglucan phosphorylase in 1963, several other specificities have been reported that differ in linkage type and/or degree of polymerization. Here, we present an overview of the progress that has been made in our understanding of β-glucan and associated β-glucobiose phosphorylases, with a special focus on their application in the synthesis of carbohydrates and related molecules. KEY POINTS: • Discovery, characteristics, and applications of β-glucan phosphorylases. • β-Glucan phosphorylases in the production of functional carbohydrates.

PMID: unknown
Title: Beta-Glucan in Foods and Health Benefits.
Year: 2021
Abstract: Many articles and manuscripts focusing on the structure, function, mechanism of action, and effects of β-glucan have been published recently [...].

PMID: unknown
Title: The phagocytic receptors of β-glucan.
Year: 2022
Abstract: Phagocytosis is a cellular process maintaining tissue balance and plays an essential role in initiating the innate immune response. The process of phagocytosis was triggered by the binding of pathogen-associated molecular patterns (PAMP) with their cell surface receptors on the phagocytes. These receptors not only perform phagocytic functions, but also bridge the gap between extracellular and intracellular communication, leading to signal transduction and the production of inflammatory mediators, which are crucial for clearing the invading pathogens and maintaining cell homeostasis. For the past few years, the application of β-glucan comes down to immunoregulation and anti-tumor territory. As a well-known PAMP, β-glucan is one of the most abundant polysaccharides in nature. By binding to specific receptors on immune cells and activating intracellular signal transduction pathways, it causes phagocytosis and promotes the release of cytokines. Further retrieval and straightening out literature related to β-glucan phagocytic receptors will help better elucidate their immunomodulatory functions. This review attempts to summarize physicochemical properties and specific processes involved in β-glucan induced phagocytosis, its phagocytic receptors, and cascade events triggered by β-glucan at the cellular and molecular levels.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

