-- ============================================================
-- Fix: Re-run recalculate_onboarding_status AFTER blockers
-- are inserted so blocked status is correctly computed.
--
-- Run this in Supabase SQL Editor after seed_onboarding_real.sql
-- ============================================================

-- First verify blockers exist with severity = 'blocking'
DO $$
DECLARE
  blocker_count integer;
BEGIN
  SELECT COUNT(*) INTO blocker_count
  FROM public.property_onboarding_blockers
  WHERE severity = 'blocking' AND resolved = false;

  RAISE NOTICE 'Unresolved blocking blockers found: %', blocker_count;
END $$;

-- Recalculate ALL 16 properties now that blockers exist
SELECT public.recalculate_onboarding_status('0a39dc44-b1d6-4c45-9e11-96c6476104e5'); -- Aurora Place
SELECT public.recalculate_onboarding_status('183f7339-e6c7-4d08-9299-422207e91f29'); -- Grand Central Living
SELECT public.recalculate_onboarding_status('39d2e354-9052-4eec-8bbf-0e39948c21ca'); -- Sunset Ridge
SELECT public.recalculate_onboarding_status('596d3791-eb69-4030-9e1b-2e3f9b2ddd09'); -- Maple Heights
SELECT public.recalculate_onboarding_status('92e9be2c-05e0-4bcc-a646-895ae83dd515'); -- Cedar Point
SELECT public.recalculate_onboarding_status('92edec9c-fa8e-4945-88f4-9c9eeaab71bb'); -- Brookstone Flats
SELECT public.recalculate_onboarding_status('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6'); -- The Meridian
SELECT public.recalculate_onboarding_status('c5a7fd3a-71be-4895-995f-3700922467d5'); -- River Lofts
SELECT public.recalculate_onboarding_status('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949'); -- Skyline Towers
SELECT public.recalculate_onboarding_status('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e'); -- Parkside Estates
SELECT public.recalculate_onboarding_status('ec6e19d8-ccee-47bb-9866-13db48ecb8e5'); -- Lakeside Commons
SELECT public.recalculate_onboarding_status('f48c0983-006e-4cfa-b0bd-18896b5c6d00'); -- Highland Square
SELECT public.recalculate_onboarding_status('f7c028a9-af8c-4f60-9a48-467ca4668cfb'); -- Pine Grove Villas
SELECT public.recalculate_onboarding_status('fc705241-30eb-448d-b3a8-416117044176'); -- Cityline Residences
SELECT public.recalculate_onboarding_status('fe7c0806-df39-4aa4-8cb5-5fd44975a66e'); -- Elmwood Court
SELECT public.recalculate_onboarding_status('ffe230e2-6caf-464c-9568-4aab4f8fb046'); -- Beacon Hill Towers

-- Verify final result
SELECT status, COUNT(*) as count
FROM public.property_onboarding_status
GROUP BY status
ORDER BY status;

-- Expected:
-- blocked      | 5
-- in-progress  | 5
-- ready        | 6
