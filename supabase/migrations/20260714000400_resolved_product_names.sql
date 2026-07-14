-- Trusted canonical product names may replace generic user input only after a
-- published ingredient list matches and the submission is forced to review.
CREATE OR REPLACE FUNCTION apply_resolved_submission_product_name()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  IF NEW.verification ->> 'verdict' = 'name_resolved'
      AND nullif(trim(NEW.verification ->> 'resolved_product_name'), '') IS NOT NULL THEN
    NEW.product_name := trim(NEW.verification ->> 'resolved_product_name');
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_product_submissions_resolved_name
  BEFORE UPDATE OF verification ON product_submissions
  FOR EACH ROW EXECUTE FUNCTION apply_resolved_submission_product_name();

-- Curator-reviewed official domain for the brand used by this submission.
INSERT INTO brand_product_domains (normalized_brand_name, domain)
VALUES ('LA ROCHE-POSAY', 'laroche-posay.us')
ON CONFLICT (normalized_brand_name, domain) DO NOTHING;
