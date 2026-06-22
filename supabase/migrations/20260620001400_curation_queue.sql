-- Curation queue. Controls which ingredients the expensive stages
-- (PubMed abstract fetch, Claude editorial generation) actually
-- process. Without this guard rail, `make editorial` would call
-- Claude on all 22k ingredients and rack up hundreds of dollars in
-- a single run.

CREATE TABLE ingredient_curation_queue (
  ingredient_id UUID PRIMARY KEY REFERENCES ingredients(id) ON DELETE CASCADE,
  priority      INTEGER NOT NULL DEFAULT 100,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes         TEXT
);

CREATE INDEX curation_queue_priority_idx
  ON ingredient_curation_queue (priority);

ALTER TABLE ingredient_curation_queue ENABLE ROW LEVEL SECURITY;
-- No public-read policy: curation status is internal.

-- Seed with launch-day must-haves. Case-insensitive match because OBF
-- entries are typically lowercase but a handful are title-cased.
-- ON CONFLICT DO NOTHING so this is safe to re-run.
INSERT INTO ingredient_curation_queue (ingredient_id, priority, notes)
SELECT i.id, 10, 'seed: launch-day must-haves'
FROM ingredients i
WHERE lower(i.inci_name) IN (
  'water', 'aqua', 'glycerin', 'niacinamide', 'retinol',
  'salicylic acid', 'ascorbic acid', 'hyaluronic acid',
  'sodium hyaluronate', 'ceramide np', 'ceramide ap',
  'squalane', 'bakuchiol', 'azelaic acid', 'lactic acid',
  'mandelic acid', 'kojic acid', 'tranexamic acid',
  'alpha-arbutin', 'allantoin', 'panthenol', 'tocopherol',
  'caffeine', 'adenosine', 'centella asiatica extract',
  'beta-glucan', 'polyglutamic acid', 'madecassoside',
  'bisabolol', 'zinc oxide', 'titanium dioxide',
  'octocrylene', 'avobenzone', 'homosalate',
  'ethylhexyl methoxycinnamate', 'glycolic acid',
  'dimethicone', 'cyclopentasiloxane', 'phenoxyethanol',
  'benzyl alcohol', 'sodium benzoate', 'potassium sorbate',
  'carbomer', 'xanthan gum', 'sodium hydroxide', 'citric acid',
  'disodium edta', 'tetrahexyldecyl ascorbate',
  'magnesium ascorbyl phosphate', 'ascorbyl glucoside',
  'resveratrol', 'ferulic acid'
)
ON CONFLICT (ingredient_id) DO NOTHING;
