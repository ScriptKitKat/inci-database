# Editorial prompt for: BENZYL ALCOHOL

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `benzyl-alcohol.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: BENZYL ALCOHOL
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Benzyl alcohol poisoning.
Year: 1983
Abstract: 

PMID: unknown
Title: Is benzyl alcohol a significant contact sensitizer?
Year: 2022
Abstract: Benzyl alcohol is a widely used preservative, solvent and fragrance material. According to published data, it is a rare sensitizer in humans. To identify characteristics and sensitization patterns of patients with positive patch test reactions to benzyl alcohol and to check the reliability of the patch test preparation benzyl alcohol 1% pet. Retrospective analysis of data from the Information Network of Departments of Dermatology (IVDK), 2010-2019. Of 70 867 patients patch tested with benzyl alcohol 1% pet., 146 (0.21%) showed a positive reaction, most of them (89%) only weakly positive. The number of doubtful and irritant reactions significantly exceeded the number of positive reactions. Reproducibility of positive test reactions was low. Among benzyl alcohol-positive patients, compared to benzyl alcohol-negative patients, there were significantly more patients with leg dermatitis (17.8% vs. 8.6%), more patients aged 40 years or more (81.5% vs. 70.5%) and more patients who were tested because of a suspected intolerance reaction to topical medications (34.9% vs. 16.6%). Concomitant positive reactions were mainly seen to fragrances, preservatives and ointment bases. Sensitization to benzyl alcohol occurs very rarely, mainly in patients with stasis dermatitis. In view of our results, benzyl alcohol cannot be regarded as a significant contact allergen, and therefore marking it as skin sensitizer 1B and labelling it with H 317 is not helpful.

PMID: unknown
Title: Benzyl alcohol: a covert fragrance.
Year: 2007
Abstract: 

PMID: unknown
Title: RIFM fragrance ingredient safety assessment, Benzyl alcohol, CAS Registry Number 100-51-6.
Year: 2015
Abstract: 

PMID: unknown
Title: Fragrance material review on benzyl alcohol.
Year: 2012
Abstract: A toxicologic and dermatologic review of benzyl alcohol when used as a fragrance ingredient is presented. Benzyl alcohol is a member of the fragrance structural group Aryl Alkyl Alcohols and is a primary alcohol. The AAAs are a structurally diverse class of fragrance ingredients that includes primary, secondary, and tertiary alkyl alcohols covalently bonded to an aryl (Ar) group, which may be either a substituted or unsubstituted benzene ring. The common structural element for the AAA fragrance ingredients is an alcohol group -C-(R1)(R2)OH and generically the AAA fragrances can be represented as an Ar-C-(R1)(R2)OH or Ar-Alkyl-C-(R1)(R2)OH group. This review contains a detailed summary of all available toxicology and dermatology papers related to this individual fragrance ingredient and is not intended as a stand-alone document. Available data for benzyl alcohol were evaluated then summarized and includes physical properties, acute toxicity, skin irritation, mucous membrane (eye) irritation, skin sensitization, elicitation, phototoxicity, photoallergy, toxicokinetics, repeated dose, reproductive toxicity, genotoxicity, and carcinogenicity data. A safety assessment of the entire Aryl Alkyl Alcohols will be published simultaneously with this document; please refer to Belsito et al. (2012) for an overall assessment of the safe use of this material and all Aryl Alkyl Alcohols in fragrances.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

