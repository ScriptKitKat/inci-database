export type Evidence = {
  source: string;
  found: boolean;
  canonical?: string;
  confidence?: number;
};

export type SubmissionToken = {
  id: string;
  position: number;
  raw_token: string;
  normalized_token: string;
  matched_ingredient_id: string | null;
  matched_name?: string | null;
  match_type: string | null;
  match_confidence: number | null;
  resolution: string;
  canonical_name: string | null;
  evidence: Evidence[];
  escalation?: string | null;
};

export type Submission = {
  id: string;
  brand_name: string;
  product_name: string;
  submitted_by: string | null;
  raw_ingredient_text: string;
  status: string;
  verification: Record<string, unknown>;
  created_at: string;
};

export type DetailData = {
  submission: Submission;
  tokens: SubmissionToken[];
  trigger: string | null;
  similarProduct: { id: string; name: string; brand: string } | null;
};
