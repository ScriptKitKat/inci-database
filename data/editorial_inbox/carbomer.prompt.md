# Editorial prompt for: CARBOMER

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `carbomer.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: CARBOMER
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: A Review of Glass-Ionomer Cements for Clinical Dentistry.
Year: 2016
Abstract: This article is an updated review of the published literature on glass-ionomer cements and covers their structure, properties and clinical uses within dentistry, with an emphasis on findings from the last five years or so. Glass-ionomers are shown to set by an acid-base reaction within 2-3 min and to form hard, reasonably strong materials with acceptable appearance. They release fluoride and are bioactive, so that they gradually develop a strong, durable interfacial ion-exchange layer at the interface with the tooth, which is responsible for their adhesion. Modified forms of glass-ionomers, namely resin-modified glass-ionomers and glass carbomer, are also described and their properties and applications covered. Physical properties of the resin-modified glass-ionomers are shown to be good, and comparable with those of conventional glass-ionomers, but biocompatibility is somewhat compromised by the presence of the resin component, 2 hydroxyethyl methacrylate. Properties of glass carbomer appear to be slightly inferior to those of the best modern conventional glass-ionomers, and there is not yet sufficient information to determine how their bioactivity compares, although they have been formulated to enhance this particular feature.

PMID: unknown
Title: Rheological characterization of topical carbomer gels neutralized to different pH.
Year: 2004
Abstract: The primary objective of this study is to perform detailed and extensive rheological characterization of rheology of carbomer (Carbopol) microgels formulated using a solvent system typically used in topical gel formulations. Solvents like glycerin and propylene glycol can alter rheology and drug delivery characteristics of topical gels owing to their different viscosities and due to the change in solvent-polymer and solvent-solvent interactions. Aqueous gels with different pH were prepared by dissolving cross-linked Carbopol polymers in a co-solvent system comprising water, propylene glycol, and glycerol and subsequently neutralizing the carboxylic groups of the polymers with triethanolamine (TEA). Oscillatory, steady, and transient shear measurements were performed to measure viscoelastic properties, temperature dependency, yield strength, and thixotropy of carbomer pharmaceutical gels. The topical pharmaceutical gels exhibit remarkable temperature stability. Flow curves obtained at different temperatures indicate Carbopol microgels show much more pseudoplastic behavior (lower power law index) compared to Carbopol gels dissolved only in water. Substantial yield strength is required to break the microgel network of the topical gels. The gel samples exhibit modest thixotropy at higher deformation rates. The theological behavior of the Carbopol microgels do not change appreciably in the pH range 5.0-8.0, and the gels can be used as effective dermatological base for topical applications.

PMID: unknown
Title: Multifunctional carbomer based ferulic acid hydrogel promotes wound healing in radiation-induced skin injury by inactivating NLRP3 inflammasome.
Year: 2024
Abstract: Radiation-induced skin injury is a significant adverse reaction to radiotherapy. However, there is a lack of effective prevention and treatment methods for this complication. Ferulic acid (FA) has been identified as an effective anti-radiation agent. Conventional administrations of FA limit the reaching of it on skin. We aimed to develop a novel FA hydrogel to facilitate the use of FA in radiation-induced skin injury. We cross-linked carbomer 940, a commonly used adjuvant, with FA at concentrations of 5%, 10%, and 15%. Sweep source optical coherence tomography system, a novel skin structure evaluation method, was applied to investigate the influence of FA on radiation-induced skin injury. Calcein-AM/PI staining, CCK8 assay, hemolysis test and scratch test were performed to investigate the biocompatibility of FA hydrogel. The reducibility of DPPH and ABTS radicals by FA hydrogel was also performed. HE staining, Masson staining, laser Doppler blood flow monitor, and OCT imaging system are used to evaluate the degree of skin tissue damage. Potential differentially expressed genes were screened via transcriptome analysis. Good biocompatibility and in vitro antioxidant ability of the FA hydrogels were observed. 10% FA hydrogel presented a better mechanical stability than 5% and 15% FA hydrogel. All three concentrations of FA remarkably promoted the recovery of radiation-induced skin injury by reducing inflammation, oxidative conidiation, skin blood flow, and accelerating skin tissue reconstruction, collagen deposition. FA hydrogel greatly inhibiting the levels of NLRP3, caspase-1, IL-18, pro-IL-1β and IL-1β in vivo and vitro levels through restraining the activation of NLRP3 inflammasome. Transcriptome analysis indicated that FA might regulate wound healing via targeting immune response, inflammatory response, cell migration, angiogenesis, hypoxia response, and cell matrix adhesion. These findings suggest that the novel FA hydrogel is a promising therapeutic method for the prevention and treatment of radiation-induced skin injury patients.

PMID: unknown
Title: Plasma-Activated Hydrogels for Microbial Disinfection.
Year: 2023
Abstract: A continuous risk from microbial infections poses a major environmental and public health challenge. As an emerging strategy for inhibiting bacterial infections, plasma-activated water (PAW) has proved to be highly effective, environmental-friendly, and non-drug resistant to a broad range of microorganisms. However, the relatively short lifetime of reactive oxygen and nitrogen species (RONS) and the high spreadability of liquid PAW inevitably limit its real-life applications. In this study, plasma-activated hydrogel (PAH) is developed to act as reactive species carrier that allow good storage and controlled slow-release of RONS to achieve long-term antibacterial effects. Three hydrogel materials, including hydroxyethyl cellulose (HEC), carbomer 940 (Carbomer), and acryloyldimethylammonium taurate/VP copolymer (AVC) are selected, and their antibacterial performances under different plasma activation conditions are investigated. It is shown that the composition of the gels plays the key role in determining their biochemical functions after the plasma activation. The antimicrobial performance of AVC is much better than that of PAW and the other two hydrogels, along with the excellent stability to maintain the antimicrobial activity for more than 14 days. The revealed mechanism of the antibacterial ability of the PAH identifies the unique combination of short-lived species (

PMID: unknown
Title: Dispersing carbomers, mixing technology matters!
Year: 2022
Abstract: Mixing dry carbomer powder with water using magneto-hydrodynamic mixing yielded carbomer dispersions with higher viscosity and increased storage modulus as compared to conventional high shear mixing.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

