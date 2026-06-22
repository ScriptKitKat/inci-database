# Editorial prompt for: SODIUM BENZOATE

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `sodium-benzoate.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: SODIUM BENZOATE
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Food additives and hyperactive behaviour in 3-year-old and 8/9-year-old children in the community: a randomised, double-blinded, placebo-controlled trial.
Year: 2007
Abstract: We undertook a randomised, double-blinded, placebo-controlled, crossover trial to test whether intake of artificial food colour and additives (AFCA) affected childhood behaviour. 153 3-year-old and 144 8/9-year-old children were included in the study. The challenge drink contained sodium benzoate and one of two AFCA mixes (A or B) or a placebo mix. The main outcome measure was a global hyperactivity aggregate (GHA), based on aggregated z-scores of observed behaviours and ratings by teachers and parents, plus, for 8/9-year-old children, a computerised test of attention. This clinical trial is registered with Current Controlled Trials (registration number ISRCTN74481308). Analysis was per protocol. 16 3-year-old children and 14 8/9-year-old children did not complete the study, for reasons unrelated to childhood behaviour. Mix A had a significantly adverse effect compared with placebo in GHA for all 3-year-old children (effect size 0.20 [95% CI 0.01-0.39], p=0.044) but not mix B versus placebo. This result persisted when analysis was restricted to 3-year-old children who consumed more than 85% of juice and had no missing data (0.32 [0.05-0.60], p=0.02). 8/9-year-old children showed a significantly adverse effect when given mix A (0.12 [0.02-0.23], p=0.023) or mix B (0.17 [0.07-0.28], p=0.001) when analysis was restricted to those children consuming at least 85% of drinks with no missing data. Artificial colours or a sodium benzoate preservative (or both) in the diet result in increased hyperactivity in 3-year-old and 8/9-year-old children in the general population.

PMID: unknown
Title: [Not Available].
Year: 2024
Abstract: A quick, simple, sensitive, efficient and stability-indicating reverse-phase ultraperformance liquid chromatographic method for the estimation of propylparaben, methylparaben and sodium benzoate in a pharmaceutical liquid oral formulation was developed. A Waters Acquity UPLC BEH C

PMID: unknown
Title: Toxicological and Teratogenic Effect of Various Food Additives: An Updated Review.
Year: 2022
Abstract: Scientific evidence is mounting that synthetic chemicals used as food additives may have harmful impacts on health. Food additives are chemicals that are added to food to keep it from spoiling, as well as to improve its colour and taste. Some are linked to negative health impacts, while others are healthy and can be ingested with little danger. According to several studies, health issues such as asthma, attention deficit hyperactivity disorder (ADHD), heart difficulties, cancer, obesity, and others are caused by harmful additives and preservatives. Some food additives may interfere with hormones and influences growth and development. It is one of the reasons why so many children are overweight. Children are more likely than adults to be exposed to these types of dietary intakes. Several food additives are used by women during pregnancy and breast feeding that are not fully safe. We must take specific precaution to avoid consuming dangerous compounds before they begin to wreak havoc on our health. This study is intended to understand how the preservatives induce different health problem in the body once it is consumed. This review focuses on some specific food additives such as sodium benzoate, aspartame, tartrazine, carrageenan, and potassium benzoate, as well as vitamin A. Long-term use of food treated with the above-mentioned food preservatives resulted in teratogenicity and other allergens, according to the study. Other health issues can be avoided in the future by using natural food additives derived from plants and other natural sources.

PMID: unknown
Title: Sodium benzoate-induced pruritus.
Year: 2006
Abstract: 

PMID: unknown
Title: Probiotics derived sodium benzoate improves social behavior of offspring exposed in the maternal immune activation through regulation of histone lysine benzoylation in astrocytes.
Year: 2025
Abstract: Autism Spectrum Disorder (ASD) is a neurodevelopmental condition increasingly linked to microbiota-gut-brain axis dysregulation, yet the causal microbial mediators and molecular mechanisms remain elusive. Based on our previously published ASD cohort, we discovered that depletion of Lactobacillus species in children with ASD correlates with exacerbated gastrointestinal symptoms and social deficits. Maternal immune activation (MIA) during pregnancy has been established as a critical environmental risk factor for ASD. Furthermore, in the MIA-induced ASD mouse model, we demonstrated that supplementation with Lactiplantibacillus plantarum, or its derived sodium benzoate (NaB), mitigates gut dysbiosis, alleviates deficits of social behavior, glutamate-glutamine levels, and neuronal activity in autistic mice. Single-cell RNA sequencing revealed that NaB restored the genes expression, like Cxcl16, in astrocytes of autistic mice, which is linked to glutamate metabolic activity between neurons and astrocytes. Further, we demonstrated that astrocytes-specific Cxcl16 knock-in hippocampus bypassed microbiota effects to restore social memory in autistic mice. Recent investigations have established NaB as key mediator of histone lysine benzoylation (Kbz), primarily through its role in generating benzoyl-CoA, the essential substrate for this epigenetic modification. Mechanistically, through integrating RNA-seq and Cut & Tag analysis, our findings revealed that NaB boosts Cxcl16 gene expression in astrocytes, possibly by increasing H3K27 benzoylation binding at enhancer regions. This highlights the therapeutic potential of probiotics-derived NaB for ASD and uncovers a novel epigenetic mechanism within the microbiota-gut-brain axis.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

