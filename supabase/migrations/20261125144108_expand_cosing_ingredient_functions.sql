CREATE OR REPLACE FUNCTION public.ingredient_functions_are_valid(function_values TEXT[])
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE PARALLEL SAFE
AS $$
  SELECT COALESCE(bool_and(value = ANY (ARRAY[
    'humectant',
    'emollient',
    'occlusive',
    'skin_conditioning',
    'barrier_supporting',
    'soothing',
    'antioxidant',
    'exfoliating',
    'keratolytic',
    'anti_acne',
    'sebum_regulating',
    'antimicrobial',
    'skin_brightening',
    'pigmentation_regulating',
    'skin_renewal',
    'firming',
    'smoothing',
    'skin_protecting',
    'uv_filtering',
    'astringent',
    'absorbent_mattifying',
    'cooling',
    'warming',
    'deodorizing',
    'self_tanning',
    'solvent',
    'surfactant_cleansing',
    'emulsifier',
    'emulsion_stabilizer',
    'viscosity_controlling',
    'gelling',
    'film_forming',
    'preservative',
    'preservative_booster',
    'chelating',
    'ph_adjusting_buffering',
    'fragrance_perfuming',
    'colorant_opacifying',
    'abrasive',
    'anticaking',
    'anticorrosive',
    'antidandruff',
    'antifoaming',
    'antiplaque',
    'antiperspirant',
    'antistatic',
    'binding',
    'bleaching',
    'bulking',
    'denaturant',
    'depilatory',
    'detangling',
    'flavoring',
    'foam_boosting',
    'foaming',
    'hair_conditioning',
    'hair_dyeing',
    'hair_fixing',
    'hair_waving_or_straightening',
    'hydrotrope',
    'masking',
    'nail_conditioning',
    'oral_care',
    'oxidizing',
    'plasticizer',
    'propellant',
    'reducing',
    'refatting',
    'refreshing',
    'stabilizing',
    'surfactant',
    'tanning',
    'tonic',
    'uv_absorber'
  ]::TEXT[])), true)
  FROM unnest(function_values) AS value;
$$;

-- Hosted databases already have this check. On older installs, do not
-- retroactively validate legacy arrays that predate the allowlist.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_constraint
    WHERE conrelid = 'public.ingredient_information'::regclass
      AND conname = 'ingredient_information_functions_allowed'
  ) THEN
    ALTER TABLE public.ingredient_information
      ADD CONSTRAINT ingredient_information_functions_allowed
      CHECK (public.ingredient_functions_are_valid(functions)) NOT VALID;
  END IF;
END;
$$;
