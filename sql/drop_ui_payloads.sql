-- Optional: remove legacy JSON snapshot table after all environments use live builders.
-- Verify: no code references `ui_payloads` (grep the repo) before running.
DROP TABLE IF EXISTS public.ui_payloads;
