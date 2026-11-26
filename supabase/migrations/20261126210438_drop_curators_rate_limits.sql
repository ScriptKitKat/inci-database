DROP FUNCTION IF EXISTS public.consume_request_rate_limit(TEXT, INTEGER, INTEGER);
DROP TABLE IF EXISTS public.request_rate_limits;

CREATE OR REPLACE FUNCTION public.is_curator()
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  SELECT false;
$$;

DROP TABLE IF EXISTS public.curators;
