# Editorial prompt for: KOJIC ACID

Paste everything below this line into Claude.ai or ChatGPT.
Save the model's JSON response as `kojic-acid.json` in this same folder.
When you've collected all responses, run:

    inci-pipeline import-editorial

---

You are an editorial writer for a skincare ingredient database. You are summarizing peer-reviewed evidence for a general audience.

Ingredient: KOJIC ACID
Declared functions (from EU CosIng): (unspecified)
Restricted in EU: no
Restricted in US: no

Source abstracts (from PubMed):
PMID: unknown
Title: Management of hyperpigmentation: Current treatments and emerging therapies.
Year: 2021
Abstract: Hyperpigmentation of the skin refers to a dermatological condition which alters the color of the skin, making it discolored or darkened. The treatments for hyperpigmentation disorders often take very long to show results and have poor patient compliance. The first-line treatment for hyperpigmentation involves topical formulations of conventional agents such as hydroquinone, kojic acid, and glycolic acid followed by oral formulations of therapeutic agents such as tranexamic acid, melatonin, and cysteamine hydrochloride. The second-line approaches include chemical peels and laser therapy given under the observation of expert professionals. However, these therapies pose certain limitations and adverse effects such as erythema, skin peeling, and drying and require long treatment duration to show visible effects. These shortcomings of the conventional treatments provided scope for further research on newer alternatives for managing hyperpigmentation. Some of these therapies include novel formulations such as solid lipid nanocarriers, liposomes, phytochemicals, platelet-rich plasma, microneedling. This review focuses on elaborating on several hyperpigmentation disorders and their mechanisms, the current, novel and emerging treatment options for management of hyperpigmentation.

PMID: unknown
Title: Kojic acid applications in cosmetic and pharmaceutical preparations.
Year: 2019
Abstract: Skin color disorders can be caused by various factors, such as excessive exposure to sunlight, aging and hormonal imbalance during pregnancy, or taking some medications. Kojic acid (KA) is a natural metabolite produced by fungi that has the ability to inhibit tyrosinase activity in synthesis of melanin. The major applications of KA and its derivatives in medicine are based on their biocompatibility, antimicrobial and antiviral, antitumor, antidiabetic, anticancer, anti-speck, anti-parasitic, and pesticidal and insecticidal properties. In addition, KA and its derivatives are used as anti-oxidant, anti-proliferative, anti-inflammatory, radio protective and skin-lightening agent in skin creams, lotions, soaps, and dental care products. KA has the ability to act as a UV protector, suppressor of hyperpigmentation in human and restrainer of melanin formation, due to its tyrosinase inhibitory activity. Also, KA could be developed as a chemo sensitizer to enhance efficacy of commercial antifungal drugs or fungicides. In general, KA and its derivatives have wide applications in cosmetics and pharmaceutical industries.

PMID: unknown
Title: Biomedical applications of tyrosinases and tyrosinase inhibitors.
Year: 2024
Abstract: Tyrosinase is involved in several human diseases, among which hypopigmentation and depigmentation conditions (vitiligo, idiopathic guttate hypomelanosis, pityriasis versicolor, pityriasis alba) and hyperpigmentations (melasma, lentigines, post-inflammatory and periorbital hyperpigmentation, cervical idiopathic poikiloderma and acanthosis nigricans). There are increasing evidences that tyrosinase plays a relevant role in the formation and progression of melanoma, a difficult to treat skin tumor. Hydroquinone, azelaic acid and tretinoin (all-trans-retinoic acid) are clinically used in the management of some hyperpigmentations, whereas many novel chemotypes acting as tyrosinase inhibitors with potential antimelanoma action are being investigated. Kojic acid, hydroquinone, its glycosylated derivative arbutin, or the resorcinol derivative rucinol are used in cosmesis in creams as skin whitening agents, whereas no antimelanoma tyrosinase inhibitor reached clinical trials so far, although thiamidol is a recently approved new tyrosinase inhibitor for the treatment of melasma. Kojic acid and vitamin C are used for avoiding vegetable/food oxidative browning due to the tyrosinase-catalyzed reactions, whereas bacterial enzymes show potential in biotechnological applications, for the production of mixed melanins, for protein cross-linking reactions, for producing phenol(s) biosensors, of for the production of L-DOPA, an anti-Parkinson's disease drug.

PMID: unknown
Title: Kojic acid.
Year: 1956
Abstract: 

PMID: unknown
Title: Fungal production of kojic acid and its industrial applications.
Year: 2023
Abstract: Kojic acid has gained its importance after it was known worldwide that the substance functions primarily as skin-lightening agent. Kojic acid plays a vital role in skin care products, as it enhances the ability to prevent exposure to UV radiation. It inhibits the tyrosinase formation which suppresses hyperpigmentation in human skin. Besides cosmetics, kojic acid is also greatly used in food, agriculture, and pharmaceuticals industries. Conversely, according to Global Industry Analysts, the Middle East, Asia, and in Africa especially, the demand of whitening cream is very high, and probably the market will reach to $31.2 billion by 2024 from $17.9 billion of 2017. The important kojic acid-producing strains were mainly belongs to the genus Aspergillus and Penicillium. Due to its commercial potential, it continues to attract the attention for its green synthesis, and the studies are still widely conducted to improve kojic acid production. Thus, the present review is focused on the current production processes, gene regulation, and limitation of its commercial production, probable reasons, and possible solutions. For the first time, detailed information on the metabolic pathway and the genes involved in kojic acid production, along with illustrations of genes, are highlighted in the present review. Demand and market applications of kojic acid and its regulatory approvals for its safer use are also discussed. KEY POINTS: • Kojic acid is an organic acid that is primarily produced by Aspergillus species. • It is mainly used in the field of health care and cosmetic industries. • Kojic acid and its derivatives seem to be safe molecules for human use.

- `what_it_does`: one sentence (under 120 chars) describing the ingredient's primary role in a formulation.
- `summary_short`: 2–3 sentences (under 400 chars), readable by a non-expert, suitable for a decode result. Include the most useful single fact a user would want to know at a glance.
- `summary_long`: 3–6 paragraphs in Markdown. Cite at least one source by PMID inline using `[PMID:12345678]` notation. Cover: mechanism, evidence quality, typical concentrations if mentioned, irritation/safety notes, common pairings or conflicts.
- `quick_facts`: array of 3–6 consumer-useful short bullet strings (<80 chars each). Examples: "Water-soluble", "Best below 10% concentration", "Pairs poorly with vitamin C".

Constraints:
- Never invent claims. If the abstracts don't support a claim, omit it.
- Never assign an overall rating ("great", "bad", etc.) — that's reserved for human curators.
- If evidence is thin, say so plainly in `summary_long`.

Write for skincare consumers, not researchers. Avoid evidence-audit language such as “typical concentration not provided,” “the abstracts do not mention,” or “no specific conflicts were identified.” Only mention a limitation if it changes how a user should interpret safety, effectiveness, or product use. Otherwise, leave that detail out.

