-- ============================================================
-- Aigentless POC — Onboarding Seed Data (REAL property IDs)
-- Based on actual CSV data from properties + units tables
-- Run AFTER migration_category2.sql
--
-- Properties (16):
--   Aurora Place, Grand Central Living, Sunset Ridge,
--   Maple Heights, Cedar Point Apartments, Brookstone Flats,
--   The Meridian, River Lofts, Skyline Towers, Parkside Estates,
--   Lakeside Commons, Highland Square, Pine Grove Villas,
--   Cityline Residences, Elmwood Court, Beacon Hill Towers
-- ============================================================

-- ============================================================
-- SECTION 1 — unit_images (based on real unit IDs)
-- Only units with images pass the media_photos checklist check
-- Strategy: 12 of 16 properties have unit images (4 missing = blockers)
-- ============================================================

INSERT INTO public.unit_images (unit_id, image_index, image_path, created_at) VALUES

-- Cedar Point Apartments: A-124, A-104 (both have images)
('00c4cd06-276a-4fa1-ade3-52b7f3155354', 1, 'units/cedar-point/A-124/living_01.jpg',  now() - interval '10 days'),
('00c4cd06-276a-4fa1-ade3-52b7f3155354', 2, 'units/cedar-point/A-124/bedroom_01.jpg', now() - interval '10 days'),
('00c4cd06-276a-4fa1-ade3-52b7f3155354', 3, 'units/cedar-point/A-124/kitchen_01.jpg', now() - interval '10 days'),
('e4102abc-f216-4cbe-9e60-a2eaa67cf1fa', 1, 'units/cedar-point/A-104/living_01.jpg',  now() - interval '10 days'),
('e4102abc-f216-4cbe-9e60-a2eaa67cf1fa', 2, 'units/cedar-point/A-104/bedroom_01.jpg', now() - interval '10 days'),

-- Skyline Towers: A-121 (has images)
('01737eb9-335d-4731-a638-9dbeba266a32', 1, 'units/skyline/A-121/living_01.jpg',  now() - interval '8 days'),
('01737eb9-335d-4731-a638-9dbeba266a32', 2, 'units/skyline/A-121/bedroom_01.jpg', now() - interval '8 days'),
('01737eb9-335d-4731-a638-9dbeba266a32', 3, 'units/skyline/A-121/bathroom_01.jpg',now() - interval '8 days'),

-- Grand Central Living: A-128 (has images), A-108 (missing — blocker)
('1da448f4-567d-4499-9a84-702323879248', 1, 'units/grand-central/A-128/living_01.jpg',  now() - interval '12 days'),
('1da448f4-567d-4499-9a84-702323879248', 2, 'units/grand-central/A-128/bedroom_01.jpg', now() - interval '12 days'),

-- River Lofts: A-122 (has images), A-102 (missing — blocker)
('1fc00df9-a32f-4e68-b5f7-5e419a4a4b84', 1, 'units/river-lofts/A-122/living_01.jpg',  now() - interval '15 days'),
('1fc00df9-a32f-4e68-b5f7-5e419a4a4b84', 2, 'units/river-lofts/A-122/bedroom_01.jpg', now() - interval '15 days'),

-- Lakeside Commons: A-126, A-106 (both have images)
('294846d1-52b0-4533-a44e-a564cec8e1bf', 1, 'units/lakeside/A-126/living_01.jpg',  now() - interval '7 days'),
('294846d1-52b0-4533-a44e-a564cec8e1bf', 2, 'units/lakeside/A-126/bedroom_01.jpg', now() - interval '7 days'),
('400eab10-fe22-444d-bf8e-257cb4fcf8cc', 1, 'units/lakeside/A-106/living_01.jpg',  now() - interval '7 days'),
('400eab10-fe22-444d-bf8e-257cb4fcf8cc', 2, 'units/lakeside/A-106/bedroom_01.jpg', now() - interval '7 days'),

-- Beacon Hill Towers: A-117, A-137 (both have images)
('37e5b03d-295c-4a24-89ca-76b9d2e080f9', 1, 'units/beacon-hill/A-117/living_01.jpg',  now() - interval '5 days'),
('37e5b03d-295c-4a24-89ca-76b9d2e080f9', 2, 'units/beacon-hill/A-117/bedroom_01.jpg', now() - interval '5 days'),
('e2647880-e4f6-49e2-86d9-42a954d047b7', 1, 'units/beacon-hill/A-137/living_01.jpg',  now() - interval '5 days'),
('e2647880-e4f6-49e2-86d9-42a954d047b7', 2, 'units/beacon-hill/A-137/bedroom_01.jpg', now() - interval '5 days'),

-- Parkside Estates: A-111 (has images), A-131 (missing — blocker)
('3b146ab2-0ab1-4f7e-95cd-f86c21b6b73f', 1, 'units/parkside/A-111/living_01.jpg',  now() - interval '9 days'),
('3b146ab2-0ab1-4f7e-95cd-f86c21b6b73f', 2, 'units/parkside/A-111/bedroom_01.jpg', now() - interval '9 days'),

-- Maple Heights: A-103, A-123 (both have images)
('4706dd37-7ef3-4ce3-9f72-f9701fae067b', 1, 'units/maple-heights/A-103/living_01.jpg',  now() - interval '20 days'),
('4706dd37-7ef3-4ce3-9f72-f9701fae067b', 2, 'units/maple-heights/A-103/bedroom_01.jpg', now() - interval '20 days'),
('bc81838d-bcd6-445f-b3ef-a532c0ffad6e', 1, 'units/maple-heights/A-123/living_01.jpg',  now() - interval '20 days'),
('bc81838d-bcd6-445f-b3ef-a532c0ffad6e', 2, 'units/maple-heights/A-123/bedroom_01.jpg', now() - interval '20 days'),

-- Cityline Residences: A-113, A-133 (both have images)
('48c11da2-46d5-4b60-bd8d-8bbe4aed1878', 1, 'units/cityline/A-113/living_01.jpg',  now() - interval '6 days'),
('48c11da2-46d5-4b60-bd8d-8bbe4aed1878', 2, 'units/cityline/A-113/bedroom_01.jpg', now() - interval '6 days'),
('8c9dc69c-7849-4254-95d4-d5140b3c8d73', 1, 'units/cityline/A-133/living_01.jpg',  now() - interval '6 days'),
('8c9dc69c-7849-4254-95d4-d5140b3c8d73', 2, 'units/cityline/A-133/bedroom_01.jpg', now() - interval '6 days'),

-- Sunset Ridge: A-109 (has images), A-129 (missing — blocker)
('6218bb17-010d-4275-877e-1e444e01497c', 1, 'units/sunset-ridge/A-109/living_01.jpg',  now() - interval '11 days'),
('6218bb17-010d-4275-877e-1e444e01497c', 2, 'units/sunset-ridge/A-109/bedroom_01.jpg', now() - interval '11 days'),

-- Pine Grove Villas: A-127, A-107 (both have images)
('6562502b-d2c0-4a58-b582-03c8425f71a2', 1, 'units/pine-grove/A-127/living_01.jpg',  now() - interval '14 days'),
('6562502b-d2c0-4a58-b582-03c8425f71a2', 2, 'units/pine-grove/A-127/bedroom_01.jpg', now() - interval '14 days'),
('f5484984-5bea-458f-9ab1-45370dd78261', 1, 'units/pine-grove/A-107/living_01.jpg',  now() - interval '14 days'),
('f5484984-5bea-458f-9ab1-45370dd78261', 2, 'units/pine-grove/A-107/bedroom_01.jpg', now() - interval '14 days'),

-- Elmwood Court: A-116, A-136 (both have images)
('65959425-c1bd-46de-b6a7-781208ded762', 1, 'units/elmwood/A-116/living_01.jpg',  now() - interval '3 days'),
('65959425-c1bd-46de-b6a7-781208ded762', 2, 'units/elmwood/A-116/bedroom_01.jpg', now() - interval '3 days'),
('93158ffc-ed3f-45e2-9acb-fc96eab91231', 1, 'units/elmwood/A-136/living_01.jpg',  now() - interval '3 days'),
('93158ffc-ed3f-45e2-9acb-fc96eab91231', 2, 'units/elmwood/A-136/bedroom_01.jpg', now() - interval '3 days'),

-- Brookstone Flats: A-114 (has images), A-134 (missing — blocker)
('6d1cfc11-2234-4bfc-81a0-dc29dbc2bd8c', 1, 'units/brookstone/A-114/living_01.jpg',  now() - interval '16 days'),
('6d1cfc11-2234-4bfc-81a0-dc29dbc2bd8c', 2, 'units/brookstone/A-114/bedroom_01.jpg', now() - interval '16 days'),

-- Highland Square: A-112, A-132 (both have images)
('702c9737-7e4c-49e4-bd80-5e5d9c961c63', 1, 'units/highland/A-112/living_01.jpg',  now() - interval '18 days'),
('702c9737-7e4c-49e4-bd80-5e5d9c961c63', 2, 'units/highland/A-112/bedroom_01.jpg', now() - interval '18 days'),
('fd84019e-80ac-4b25-821a-fdd03df45bec', 1, 'units/highland/A-132/living_01.jpg',  now() - interval '18 days'),
('fd84019e-80ac-4b25-821a-fdd03df45bec', 2, 'units/highland/A-132/bedroom_01.jpg', now() - interval '18 days'),

-- The Meridian: A-138, A-118 (both have images)
('73bbe383-003e-431b-a285-9fc6d6296d11', 1, 'units/meridian/A-138/living_01.jpg',  now() - interval '22 days'),
('73bbe383-003e-431b-a285-9fc6d6296d11', 2, 'units/meridian/A-138/bedroom_01.jpg', now() - interval '22 days'),
('afa13298-9d38-4cac-88eb-9a82d7fa5aec', 1, 'units/meridian/A-118/living_01.jpg',  now() - interval '22 days'),
('afa13298-9d38-4cac-88eb-9a82d7fa5aec', 2, 'units/meridian/A-118/bedroom_01.jpg', now() - interval '22 days')

-- Aurora Place: A-119 — NO unit images (complete blocker)
-- No rows inserted for f702d151-11f3-4f06-982c-ca7f07e88b94

ON CONFLICT DO NOTHING;


-- ============================================================
-- SECTION 2 — property_onboarding_sections
-- 6 sections × 16 properties = 96 rows
-- Designed so Figma screens show: ready/in-progress/blocked mix
-- ============================================================

INSERT INTO public.property_onboarding_sections
  (property_id, section, completion_pct, status, metadata) VALUES

-- ── Aurora Place (0a39dc44) — BLOCKED (55%) ─────────────────
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','units_floor_plans', 80,'in-progress', '{"units_added":1,"note":"Only 1 of 200 units added"}'),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','amenities',         60,'in-progress', '{"amenities_count":2,"described":1}'),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','media_photos',       0,'not-started', '{"uploaded":0,"required":200,"note":"No unit photos uploaded"}'),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','content_faqs',      40,'in-progress', '{"completed":4,"total":10}'),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','integrations',      20,'in-progress', '{"connected":1,"required":5}'),

-- ── Grand Central Living (183f7339) — IN-PROGRESS (72%) ─────
('183f7339-e6c7-4d08-9299-422207e91f29','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('183f7339-e6c7-4d08-9299-422207e91f29','units_floor_plans', 90,'in-progress', '{"units_added":2,"note":"2 of 200 units added"}'),
('183f7339-e6c7-4d08-9299-422207e91f29','amenities',         80,'in-progress', '{"amenities_count":2,"described":2}'),
('183f7339-e6c7-4d08-9299-422207e91f29','media_photos',      50,'in-progress', '{"uploaded":1,"required":2,"missing":["A-108"]}'),
('183f7339-e6c7-4d08-9299-422207e91f29','content_faqs',      70,'in-progress', '{"completed":7,"total":10}'),
('183f7339-e6c7-4d08-9299-422207e91f29','integrations',      60,'in-progress', '{"connected":3,"required":5}'),

-- ── Sunset Ridge (39d2e354) — BLOCKED (65%) ──────────────────
('39d2e354-9052-4eec-8bbf-0e39948c21ca','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','units_floor_plans', 90,'in-progress', '{"units_added":2,"note":"2 of 200 units added"}'),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','amenities',         70,'in-progress', '{"amenities_count":2,"described":1}'),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','media_photos',      50,'in-progress', '{"uploaded":1,"required":2,"missing":["A-129"]}'),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','content_faqs',      50,'blocked',     '{"completed":5,"total":10,"missing":["Pet policy FAQ","Parking FAQ"]}'),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','integrations',      40,'in-progress', '{"connected":2,"required":5}'),

-- ── Maple Heights (596d3791) — READY (100%) ─────────────────
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','units_floor_plans',100,'complete',    '{"units_added":2,"floor_plans":2}'),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','content_faqs',     100,'complete',    '{"completed":10,"total":10}'),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- ── Cedar Point Apartments (92e9be2c) — READY (100%) ────────
('92e9be2c-05e0-4bcc-a646-895ae83dd515','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','units_floor_plans',100,'complete',    '{"units_added":2,"floor_plans":2}'),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','content_faqs',     100,'complete',    '{"completed":10,"total":10}'),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- ── Brookstone Flats (92edec9c) — BLOCKED (70%) ─────────────
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','units_floor_plans', 90,'in-progress', '{"units_added":2,"note":"2 of 200 units added"}'),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','amenities',         80,'in-progress', '{"amenities_count":2,"described":2}'),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','media_photos',      50,'in-progress', '{"uploaded":1,"required":2,"missing":["A-134"]}'),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','content_faqs',      50,'blocked',     '{"completed":5,"total":10,"missing":["Pet policy FAQ","Lease break policy"]}'),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','integrations',      60,'in-progress', '{"connected":3,"required":5}'),

-- ── The Meridian (a8d0cd37) — READY (100%) ──────────────────
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','units_floor_plans',100,'complete',    '{"units_added":2,"floor_plans":2}'),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','content_faqs',     100,'complete',    '{"completed":10,"total":10}'),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- ── River Lofts (c5a7fd3a) — BLOCKED (78%) ──────────────────
('c5a7fd3a-71be-4895-995f-3700922467d5','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('c5a7fd3a-71be-4895-995f-3700922467d5','units_floor_plans', 90,'in-progress', '{"units_added":2,"note":"2 of 200 units added"}'),
('c5a7fd3a-71be-4895-995f-3700922467d5','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('c5a7fd3a-71be-4895-995f-3700922467d5','media_photos',      50,'in-progress', '{"uploaded":1,"required":2,"missing":["A-102"]}'),
('c5a7fd3a-71be-4895-995f-3700922467d5','content_faqs',      70,'blocked',     '{"completed":7,"total":10,"missing":["Pet policy FAQ","Parking FAQ","Lease break policy"]}'),
('c5a7fd3a-71be-4895-995f-3700922467d5','integrations',      80,'in-progress', '{"connected":4,"required":5,"pending":["Yardi Voyager PMS sync"]}'),

-- ── Skyline Towers (e3ff8f2a) — IN-PROGRESS (83%) ───────────
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','units_floor_plans', 90,'in-progress', '{"units_added":1,"note":"1 of 200 units added"}'),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','media_photos',     100,'complete',    '{"uploaded":1,"required":1}'),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','content_faqs',      80,'in-progress', '{"completed":8,"total":10}'),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','integrations',      80,'in-progress', '{"connected":4,"required":5}'),

-- ── Parkside Estates (e6e0e36b) — BLOCKED (68%) ─────────────
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','units_floor_plans', 80,'in-progress', '{"units_added":2,"note":"2 of 200 units added"}'),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','amenities',         60,'in-progress', '{"amenities_count":2,"described":1}'),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','media_photos',      50,'in-progress', '{"uploaded":1,"required":2,"missing":["A-131"]}'),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','content_faqs',      50,'blocked',     '{"completed":5,"total":10,"missing":["Pet policy FAQ","Parking FAQ"]}'),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','integrations',      60,'in-progress', '{"connected":3,"required":5}'),

-- ── Lakeside Commons (ec6e19d8) — READY (100%) ──────────────
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','units_floor_plans',100,'complete',    '{"units_added":2,"floor_plans":2}'),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','content_faqs',     100,'complete',    '{"completed":10,"total":10}'),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- ── Highland Square (f48c0983) — READY (100%) ───────────────
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','units_floor_plans',100,'complete',    '{"units_added":2,"floor_plans":2}'),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','content_faqs',     100,'complete',    '{"completed":10,"total":10}'),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- ── Pine Grove Villas (f7c028a9) — IN-PROGRESS (87%) ────────
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','units_floor_plans', 90,'in-progress', '{"units_added":2,"note":"2 of 200 units added"}'),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','content_faqs',      80,'in-progress', '{"completed":8,"total":10}'),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','integrations',      80,'in-progress', '{"connected":4,"required":5}'),

-- ── Cityline Residences (fc705241) — IN-PROGRESS (88%) ──────
('fc705241-30eb-448d-b3a8-416117044176','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('fc705241-30eb-448d-b3a8-416117044176','units_floor_plans', 90,'in-progress', '{"units_added":2,"note":"2 of 200 units added"}'),
('fc705241-30eb-448d-b3a8-416117044176','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('fc705241-30eb-448d-b3a8-416117044176','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('fc705241-30eb-448d-b3a8-416117044176','content_faqs',      80,'in-progress', '{"completed":8,"total":10}'),
('fc705241-30eb-448d-b3a8-416117044176','integrations',      80,'in-progress', '{"connected":4,"required":5}'),

-- ── Elmwood Court (fe7c0806) — IN-PROGRESS (90%) ────────────
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','units_floor_plans',100,'complete',    '{"units_added":2,"floor_plans":2}'),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','content_faqs',      80,'in-progress', '{"completed":8,"total":10}'),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','integrations',      80,'in-progress', '{"connected":4,"required":5}'),

-- ── Beacon Hill Towers (ffe230e2) — READY (100%) ─────────────
('ffe230e2-6caf-464c-9568-4aab4f8fb046','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','units_floor_plans',100,'complete',    '{"units_added":2,"floor_plans":2}'),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','amenities',        100,'complete',    '{"amenities_count":2,"described":2}'),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','media_photos',     100,'complete',    '{"uploaded":2,"required":2}'),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','content_faqs',     100,'complete',    '{"completed":10,"total":10}'),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','integrations',     100,'complete',    '{"connected":5,"required":5}')

ON CONFLICT (property_id, section) DO UPDATE SET
  completion_pct = EXCLUDED.completion_pct,
  status         = EXCLUDED.status,
  metadata       = EXCLUDED.metadata,
  updated_at     = now();


-- ============================================================
-- SECTION 3 — property_onboarding_status
-- Calculated from sections via recalculate_onboarding_status()
-- Ready: 5 | Blocked: 4 | In-Progress: 7
-- ============================================================

SELECT public.recalculate_onboarding_status('0a39dc44-b1d6-4c45-9e11-96c6476104e5');
SELECT public.recalculate_onboarding_status('183f7339-e6c7-4d08-9299-422207e91f29');
SELECT public.recalculate_onboarding_status('39d2e354-9052-4eec-8bbf-0e39948c21ca');
SELECT public.recalculate_onboarding_status('596d3791-eb69-4030-9e1b-2e3f9b2ddd09');
SELECT public.recalculate_onboarding_status('92e9be2c-05e0-4bcc-a646-895ae83dd515');
SELECT public.recalculate_onboarding_status('92edec9c-fa8e-4945-88f4-9c9eeaab71bb');
SELECT public.recalculate_onboarding_status('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6');
SELECT public.recalculate_onboarding_status('c5a7fd3a-71be-4895-995f-3700922467d5');
SELECT public.recalculate_onboarding_status('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949');
SELECT public.recalculate_onboarding_status('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e');
SELECT public.recalculate_onboarding_status('ec6e19d8-ccee-47bb-9866-13db48ecb8e5');
SELECT public.recalculate_onboarding_status('f48c0983-006e-4cfa-b0bd-18896b5c6d00');
SELECT public.recalculate_onboarding_status('f7c028a9-af8c-4f60-9a48-467ca4668cfb');
SELECT public.recalculate_onboarding_status('fc705241-30eb-448d-b3a8-416117044176');
SELECT public.recalculate_onboarding_status('fe7c0806-df39-4aa4-8cb5-5fd44975a66e');
SELECT public.recalculate_onboarding_status('ffe230e2-6caf-464c-9568-4aab4f8fb046');


-- ============================================================
-- SECTION 4 — property_onboarding_blockers
-- Active blockers drive what shows in the UI right panel
-- ============================================================

INSERT INTO public.property_onboarding_blockers
  (property_id, section, type, severity, message, description, action, ai_can_fix, resolved) VALUES

-- Aurora Place: missing unit photos (blocking)
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','media_photos','missing_media','blocking',
 'No unit photos uploaded',
 'Unit A-119 is missing all listing photos. Media is required before go-live.',
 'Upload at least 2 photos for unit A-119',
 false, false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','content_faqs','missing_content','warning',
 'Missing 6 FAQ categories',
 '6 FAQ categories are incomplete including pet policy and parking.',
 'Generate missing FAQs using AI content generator',
 true, false),

-- Sunset Ridge: pet policy missing (blocking), missing photo
('39d2e354-9052-4eec-8bbf-0e39948c21ca','content_faqs','missing_content','blocking',
 'Pet policy FAQ required',
 'Pet policy FAQ is required before listing on Apartments.com and Zillow.',
 'Generate pet policy FAQ or enter manually',
 true, false),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','media_photos','missing_media','warning',
 '1 unit photo missing',
 'Unit A-129 is missing professional listing photos.',
 'Upload at least 2 photos for unit A-129',
 false, false),

-- Brookstone Flats: pet policy + lease break (blocking)
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','content_faqs','missing_content','blocking',
 'Lease break policy missing',
 'Lease break policy FAQ is a legal requirement before listing.',
 'Add lease break policy FAQ using AI generation or legal template',
 true, false),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','media_photos','missing_media','warning',
 '1 unit photo missing',
 'Unit A-134 is missing professional listing photos.',
 'Upload at least 2 photos for unit A-134',
 false, false),

-- River Lofts: pet policy + PMS sync (blocking)
('c5a7fd3a-71be-4895-995f-3700922467d5','content_faqs','missing_content','blocking',
 'Missing pet policy FAQ',
 'Pet policy FAQ required before listing goes live on Apartments.com and Zillow.',
 'Generate pet policy FAQ or enter manually',
 true, false),
('c5a7fd3a-71be-4895-995f-3700922467d5','integrations','sync_pending','warning',
 'PMS sync pending',
 'Yardi Voyager PMS sync has not completed. Unit availability may be stale.',
 'Trigger manual sync or check Yardi API credentials',
 false, false),
('c5a7fd3a-71be-4895-995f-3700922467d5','media_photos','missing_media','warning',
 '1 unit photo missing',
 'Unit A-102 is missing professional listing photos.',
 'Upload at least 2 photos for unit A-102',
 false, false),

-- Parkside Estates: pet policy (blocking), missing photo
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','content_faqs','missing_content','blocking',
 'Pet policy FAQ required',
 'Pet policy FAQ is required before listing can go live.',
 'Generate pet policy FAQ or enter manually',
 true, false),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','media_photos','missing_media','warning',
 '1 unit photo missing',
 'Unit A-131 is missing professional listing photos.',
 'Upload at least 2 photos for unit A-131',
 false, false),

-- Grand Central Living: missing photo only (warning)
('183f7339-e6c7-4d08-9299-422207e91f29','media_photos','missing_media','warning',
 '1 unit photo missing',
 'Unit A-108 is missing professional listing photos. Quality score reduced.',
 'Upload at least 2 photos for unit A-108',
 false, false),

-- Pine Grove Villas: 2 FAQs missing (warning)
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','content_faqs','missing_content','warning',
 '2 FAQ categories incomplete',
 'Short-term rental policy and lease break policy FAQs are missing.',
 'Generate missing FAQs using AI content generator',
 true, false),

-- Cityline Residences: 2 FAQs missing (warning)
('fc705241-30eb-448d-b3a8-416117044176','content_faqs','missing_content','warning',
 '2 FAQ categories incomplete',
 'Guest policy and noise policy FAQs are missing.',
 'Generate missing FAQs using AI content generator',
 true, false),

-- Elmwood Court: 2 FAQs missing (warning)
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','content_faqs','missing_content','warning',
 '2 FAQ categories incomplete',
 'Short-term rental and subletting policy FAQs are missing.',
 'Generate missing FAQs using AI content generator',
 true, false),

-- Skyline Towers: 2 FAQs (warning, no blocker)
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','content_faqs','missing_content','warning',
 '2 FAQ categories incomplete',
 'Move-out policy and subletting policy FAQs are missing.',
 'Generate missing FAQs using AI content generator',
 true, false)

ON CONFLICT DO NOTHING;


-- ============================================================
-- SECTION 5 — property_faqs
-- Complete FAQs for ready properties, partial for in-progress,
-- minimal for blocked. Categories match the checklist items.
-- ============================================================

INSERT INTO public.property_faqs
  (property_id, question, answer, category, ai_generated, is_published) VALUES

-- ── Maple Heights (596d3791) — READY: all 10 published ──────
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','What is the lease term?','We offer 6, 9, and 12-month lease terms. Month-to-month available after initial lease at a premium.','lease',false,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','What is the pet policy?','Cats and dogs welcome, maximum 2 pets up to 60 lbs. $400 pet deposit, $60/month pet rent.','pet_policy',true,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','What is the parking policy?','One assigned covered space included per unit. Additional parking $100/month.','parking',false,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','What utilities are included?','Water, sewer, and trash included. Electricity and gas metered individually.','utilities',false,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','How do I submit a maintenance request?','Submit via the resident portal or call (555) 555-0200. Emergency line available 24/7.','maintenance',false,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','What is the guest policy?','Guests may stay up to 7 consecutive nights. Long-term guests must be added to the lease.','guest',false,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','Is there a noise policy?','Quiet hours are 10pm–8am Sunday–Thursday and 11pm–9am Friday–Saturday.','noise',false,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','What is the lease break policy?','60-day notice required. Break fee equals 1.5 months rent.','lease',true,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','What is the move-in process?','Schedule move-in online. Elevator reserved in 2-hour slots, 9am–6pm weekdays.','move_in',false,true),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','Is renters insurance required?','Yes, $100,000 minimum liability coverage required from all residents.','general',false,true),

-- ── Cedar Point Apartments (92e9be2c) — READY: all 10 published
('92e9be2c-05e0-4bcc-a646-895ae83dd515','What is the lease term?','Standard 12-month lease. 6-month leases available at a 10% monthly premium.','lease',false,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','What is the pet policy?','We welcome cats and dogs up to 80 lbs. Limit 2 pets. $500 deposit, $75/month pet rent.','pet_policy',true,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','What is the parking policy?','One assigned garage space included. Additional spaces at $150/month.','parking',false,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','What utilities are included?','Water, trash, and recycling included. Gas and electric billed separately.','utilities',false,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','How do I submit a maintenance request?','Use the resident app or call our 24/7 maintenance line. Emergency response within 2 hours.','maintenance',false,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','What is the guest policy?','Overnight guests allowed up to 10 days/month. Long-term guests must be added to the lease.','guest',false,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','Is there a noise policy?','Quiet hours 10pm–8am daily. Pool and rooftop close at 11pm.','noise',false,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','What is the lease break policy?','Early termination requires 60-day notice and a fee equal to 2 months rent.','lease',true,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','What is the move-in process?','Move-ins by appointment only, 9am–6pm weekdays. Building elevator reserved in 2-hour blocks.','move_in',false,true),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','Is renters insurance required?','Yes. Minimum $100,000 liability. You may be added to our group policy for $12/month.','general',false,true),

-- ── The Meridian (a8d0cd37) — READY: all 10 published ───────
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','What is the lease term?','We offer flexible 6, 9, and 12-month lease options.','lease',false,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','What is the pet policy?','Dogs and cats welcome up to 50 lbs. Maximum 2 pets. $350 deposit, $50/month pet rent.','pet_policy',true,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','What is the parking policy?','Covered parking included with every unit. Guest parking available in visitor lot.','parking',false,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','What utilities are included?','Water and trash included. Electricity and internet are resident responsibility.','utilities',false,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','How do I submit a maintenance request?','Submit requests 24/7 through our resident portal or call (555) 555-0300.','maintenance',false,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','What is the guest policy?','Guests may stay for up to 14 consecutive days with advance notice.','guest',false,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','Is there a noise policy?','Quiet hours enforced from 10pm to 8am on all days.','noise',false,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','What is the lease break policy?','Lease breaks require 45-day notice and a fee of 1.5 months rent.','lease',true,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','What is the move-in process?','Move-ins scheduled Mon–Sat 9am–5pm. Keys issued after final walkthrough.','move_in',false,true),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','Is renters insurance required?','Yes, all residents must provide proof of renters insurance prior to move-in.','general',false,true),

-- ── Lakeside Commons (ec6e19d8) — READY: all 10 published ───
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','What is the lease term?','12-month standard lease. Short-term options available on request.','lease',false,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','What is the pet policy?','Cats and small dogs under 40 lbs welcome. $300 deposit, $50/month pet rent.','pet_policy',true,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','What is the parking policy?','One surface parking space per unit included at no charge.','parking',false,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','What utilities are included?','Water, sewer, and trash collection included in monthly rent.','utilities',false,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','How do I submit a maintenance request?','Call (555) 555-0400 or submit online through the resident portal.','maintenance',false,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','What is the guest policy?','Guests welcome for up to 7 consecutive nights per month.','guest',false,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','Is there a noise policy?','Quiet hours are 10pm–8am. Community standards enforced year-round.','noise',false,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','What is the lease break policy?','30-day notice required. Break fee of 1 month rent applies.','lease',true,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','What is the move-in process?','Move-in appointments available weekdays 9am–5pm and Saturdays 10am–2pm.','move_in',false,true),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','Is renters insurance required?','Yes. Proof of insurance with $50,000 minimum coverage required at lease signing.','general',false,true),

-- ── Highland Square (f48c0983) — READY: all 10 published ────
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','What is the lease term?','Standard 12-month lease with options for 6 or 9-month terms.','lease',false,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','What is the pet policy?','Dogs and cats allowed up to 65 lbs. $450 deposit, $65/month pet rent. Max 2 pets.','pet_policy',true,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','What is the parking policy?','One assigned space included. Additional uncovered parking available for $75/month.','parking',false,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','What utilities are included?','Water and trash service included. Gas and electricity are resident responsibility.','utilities',false,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','How do I submit a maintenance request?','Use the Highland Square app or email maintenance@highlandsquare.com.','maintenance',false,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','What is the guest policy?','Guests may stay up to 10 consecutive days. Repeat stays require management notice.','guest',false,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','Is there a noise policy?','Quiet hours 10pm–8am daily. Outdoor amenities close at 10pm.','noise',false,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','What is the lease break policy?','60-day written notice required. Break fee of 2 months rent.','lease',true,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','What is the move-in process?','Schedule via resident portal. Key handoff conducted with community manager.','move_in',false,true),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','Is renters insurance required?','Required. $100,000 minimum liability. Policy must name property as additional insured.','general',false,true),

-- ── Beacon Hill Towers (ffe230e2) — READY: all 10 published ─
('ffe230e2-6caf-464c-9568-4aab4f8fb046','What is the lease term?','We offer 12-month leases with the option to renew.','lease',false,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','What is the pet policy?','Cats and dogs welcome. Max weight 75 lbs. $400 pet deposit, $70/month pet rent.','pet_policy',true,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','What is the parking policy?','Structured parking included for all residents. EV charging available.','parking',false,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','What utilities are included?','Water, trash, and recycling are covered. Electricity and gas are billed to resident.','utilities',false,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','How do I submit a maintenance request?','24/7 maintenance portal or call (555) 555-0500. Urgent issues handled within 4 hours.','maintenance',false,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','What is the guest policy?','Guests welcome up to 14 nights per month. Notify management for stays over 7 days.','guest',false,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','Is there a noise policy?','Quiet hours from 10pm to 8am. Pool and rooftop close at 10pm on weeknights.','noise',false,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','What is the lease break policy?','Early termination requires 60 days notice and a fee equal to 2 months rent.','lease',true,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','What is the move-in process?','Move-ins by appointment Mon–Sat. Check-in with concierge and complete inspection form.','move_in',false,true),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','Is renters insurance required?','Yes, required. Upload proof of insurance to the resident portal before move-in.','general',false,true),

-- ── In-progress properties: partial FAQs (7-8 published) ────
-- Grand Central Living (183f7339) — 7 published
('183f7339-e6c7-4d08-9299-422207e91f29','What is the lease term?','12-month standard lease available.','lease',false,true),
('183f7339-e6c7-4d08-9299-422207e91f29','What is the pet policy?','Cats and dogs welcome up to 50 lbs. $350 deposit, $55/month pet rent.','pet_policy',true,true),
('183f7339-e6c7-4d08-9299-422207e91f29','What utilities are included?','Water and trash included.','utilities',false,true),
('183f7339-e6c7-4d08-9299-422207e91f29','How do I submit a maintenance request?','Submit via our online portal or call the office.','maintenance',false,true),
('183f7339-e6c7-4d08-9299-422207e91f29','What is the guest policy?','Guests may stay up to 7 consecutive nights.','guest',false,true),
('183f7339-e6c7-4d08-9299-422207e91f29','Is there a noise policy?','Quiet hours from 10pm to 8am daily.','noise',false,true),
('183f7339-e6c7-4d08-9299-422207e91f29','Is renters insurance required?','Yes, $100,000 minimum coverage required.','general',false,true),
('183f7339-e6c7-4d08-9299-422207e91f29','What is the parking policy?','','parking',false,false),
('183f7339-e6c7-4d08-9299-422207e91f29','What is the lease break policy?','','lease',false,false),
('183f7339-e6c7-4d08-9299-422207e91f29','What is the move-in process?','','move_in',false,false),

-- Skyline Towers (e3ff8f2a) — 8 published
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','What is the lease term?','12-month leases. 6-month available at premium.','lease',false,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','What is the pet policy?','Dogs and cats up to 80 lbs. Max 2 pets. $500 deposit, $75/month pet rent.','pet_policy',true,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','What is the parking policy?','Assigned garage space included. Additional parking $150/month.','parking',false,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','What utilities are included?','Water, trash, and recycling included.','utilities',false,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','How do I submit a maintenance request?','24/7 maintenance line. Emergency response guaranteed within 2 hours.','maintenance',false,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','What is the guest policy?','Guests allowed up to 10 nights/month.','guest',false,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','Is there a noise policy?','Quiet hours 10pm–8am. Amenities close at 11pm.','noise',false,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','What is the lease break policy?','60-day notice. Break fee of 2 months rent.','lease',true,true),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','What is the move-in process?','','move_in',false,false),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','Is renters insurance required?','','general',false,false),

-- Pine Grove Villas (f7c028a9) — 8 published
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','What is the lease term?','12-month standard lease.','lease',false,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','What is the pet policy?','Cats and dogs up to 60 lbs. $400 deposit, $60/month pet rent.','pet_policy',true,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','What is the parking policy?','Covered parking included per unit.','parking',false,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','What utilities are included?','Water and trash included.','utilities',false,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','How do I submit a maintenance request?','Online portal or phone. Emergency line available.','maintenance',false,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','What is the guest policy?','Guests up to 7 consecutive nights.','guest',false,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','Is there a noise policy?','Quiet hours 10pm–8am daily.','noise',false,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','Is renters insurance required?','Yes, $100,000 minimum liability required.','general',false,true),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','What is the lease break policy?','','lease',false,false),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','What is the move-in process?','','move_in',false,false),

-- Cityline Residences (fc705241) — 8 published
('fc705241-30eb-448d-b3a8-416117044176','What is the lease term?','12-month lease standard.','lease',false,true),
('fc705241-30eb-448d-b3a8-416117044176','What is the pet policy?','Dogs and cats welcome. Max 2 pets, 65 lbs. $425 deposit, $60/month.','pet_policy',true,true),
('fc705241-30eb-448d-b3a8-416117044176','What is the parking policy?','One space included per unit. Extra spaces $80/month.','parking',false,true),
('fc705241-30eb-448d-b3a8-416117044176','What utilities are included?','Water, sewer, and trash included.','utilities',false,true),
('fc705241-30eb-448d-b3a8-416117044176','How do I submit a maintenance request?','Resident portal or phone line 24/7.','maintenance',false,true),
('fc705241-30eb-448d-b3a8-416117044176','Is there a noise policy?','Quiet hours 10pm–8am.','noise',false,true),
('fc705241-30eb-448d-b3a8-416117044176','What is the lease break policy?','60-day notice, 1.5 months break fee.','lease',true,true),
('fc705241-30eb-448d-b3a8-416117044176','Is renters insurance required?','Required, $100,000 minimum.','general',false,true),
('fc705241-30eb-448d-b3a8-416117044176','What is the guest policy?','','guest',false,false),
('fc705241-30eb-448d-b3a8-416117044176','What is the move-in process?','','move_in',false,false),

-- Elmwood Court (fe7c0806) — 8 published
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','What is the lease term?','12-month and 6-month lease options.','lease',false,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','What is the pet policy?','Cats and dogs up to 55 lbs. $375 deposit, $55/month pet rent.','pet_policy',true,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','What is the parking policy?','Surface parking space included. No additional charge.','parking',false,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','What utilities are included?','Water and trash included.','utilities',false,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','How do I submit a maintenance request?','Submit requests through the resident portal 24/7.','maintenance',false,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','What is the guest policy?','Guests up to 7 nights. Extended stays require approval.','guest',false,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','Is there a noise policy?','Quiet hours 10pm–8am every night.','noise',false,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','Is renters insurance required?','Yes, $100,000 minimum liability.','general',false,true),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','What is the lease break policy?','','lease',false,false),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','What is the move-in process?','','move_in',false,false),

-- ── Blocked properties: minimal FAQs ────────────────────────
-- River Lofts (c5a7fd3a) — 7 published, pet policy empty
('c5a7fd3a-71be-4895-995f-3700922467d5','What is the lease term?','6, 9, and 12-month lease terms available.','lease',false,true),
('c5a7fd3a-71be-4895-995f-3700922467d5','What utilities are included?','Water, trash, and recycling included.','utilities',false,true),
('c5a7fd3a-71be-4895-995f-3700922467d5','How do I submit a maintenance request?','Submit via resident portal or call maintenance hotline.','maintenance',false,true),
('c5a7fd3a-71be-4895-995f-3700922467d5','What is the guest policy?','Guests may stay up to 14 consecutive days.','guest',false,true),
('c5a7fd3a-71be-4895-995f-3700922467d5','Is there a noise policy?','Quiet hours 10pm–8am Sunday–Thursday.','noise',false,true),
('c5a7fd3a-71be-4895-995f-3700922467d5','What is the lease break policy?','60-day notice required. Break fee of 2 months rent.','lease',true,true),
('c5a7fd3a-71be-4895-995f-3700922467d5','Is renters insurance required?','Yes, required prior to move-in.','general',false,true),
('c5a7fd3a-71be-4895-995f-3700922467d5','What is the pet policy?','','pet_policy',false,false),
('c5a7fd3a-71be-4895-995f-3700922467d5','What is the parking policy?','','parking',false,false),
('c5a7fd3a-71be-4895-995f-3700922467d5','What is the move-in process?','','move_in',false,false),

-- Aurora Place (0a39dc44) — 4 published
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','What is the lease term?','12-month lease terms.','lease',false,true),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','What utilities are included?','Water and trash included.','utilities',false,true),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','How do I submit a maintenance request?','Call the office during business hours.','maintenance',false,true),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','Is renters insurance required?','Strongly recommended.','general',false,true),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','What is the pet policy?','','pet_policy',false,false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','What is the parking policy?','','parking',false,false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','What is the guest policy?','','guest',false,false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','Is there a noise policy?','','noise',false,false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','What is the lease break policy?','','lease',false,false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','What is the move-in process?','','move_in',false,false)

ON CONFLICT DO NOTHING;


-- ============================================================
-- SECTION 6 — property_amenities
-- Full descriptions for ready properties, partial for others
-- ============================================================

INSERT INTO public.property_amenities
  (property_id, name, description, category, ai_generated) VALUES

-- Maple Heights (596d3791) — complete
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','Gym','State-of-the-art fitness center with cardio, free weights, and TRX. Open 24/7.','wellness',false),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','Pool','Resort-style pool with sun deck and lounge chairs. Open May–October.','outdoor',false),

-- Cedar Point Apartments (92e9be2c) — complete
('92e9be2c-05e0-4bcc-a646-895ae83dd515','Gym','Modern fitness center with strength and cardio equipment. Open 24/7.','wellness',false),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','Pool','Outdoor pool with heated spa and sun loungers.','outdoor',false),

-- The Meridian (a8d0cd37) — complete
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','Gym','Fully equipped gym with Peloton bikes and free weights. Open 24/7.','wellness',false),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','Pool','Heated outdoor pool with tanning deck and private cabanas.','outdoor',false),

-- Lakeside Commons (ec6e19d8) — complete
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','Gym','Community fitness center with cardio and weight training equipment.','wellness',false),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','Pool','Lakeside pool with panoramic views and lounge seating.','outdoor',false),

-- Highland Square (f48c0983) — complete
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','Gym','Premium fitness center with classes and personal training sessions available.','wellness',false),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','Pool','Temperature-controlled outdoor pool with sun deck.','outdoor',false),

-- Beacon Hill Towers (ffe230e2) — complete
('ffe230e2-6caf-464c-9568-4aab4f8fb046','Gym','High-end fitness center with studio space for group classes.','wellness',false),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','Pool','Rooftop pool with city views. Open year-round.','outdoor',false),

-- In-progress properties — partial descriptions
('183f7339-e6c7-4d08-9299-422207e91f29','Gym','Modern fitness center with cardio and strength training equipment.','wellness',false),
('183f7339-e6c7-4d08-9299-422207e91f29','Pool','','outdoor',false),

('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','Gym','Fitness center with free weights and cardio machines.','wellness',false),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','Pool','Community pool with sun deck.','outdoor',false),

('f7c028a9-af8c-4f60-9a48-467ca4668cfb','Gym','Well-equipped fitness center open to all residents.','wellness',false),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','Pool','','outdoor',false),

('fc705241-30eb-448d-b3a8-416117044176','Gym','Fitness center with cardio equipment and free weights.','wellness',false),
('fc705241-30eb-448d-b3a8-416117044176','Pool','Seasonal outdoor pool with loungers.','outdoor',false),

('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','Gym','Community gym with essential cardio and strength equipment.','wellness',false),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','Pool','','outdoor',false),

-- Blocked properties — minimal/empty
('c5a7fd3a-71be-4895-995f-3700922467d5','Gym','','wellness',false),
('c5a7fd3a-71be-4895-995f-3700922467d5','Pool','','outdoor',false),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','Gym','','wellness',false),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','Pool','','outdoor',false),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','Gym','','wellness',false),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','Pool','','outdoor',false),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','Gym','','wellness',false),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','Pool','','outdoor',false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','Gym','Community gym.','wellness',false),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','Pool','','outdoor',false)

ON CONFLICT DO NOTHING;


-- ============================================================
-- SECTION 7 — property_integration_status
-- 5 integrations × 16 properties = 80 rows
-- Ready properties: all 5 connected
-- Blocked: 3-4 connected, 1 missing
-- In-progress: 2-4 connected
-- ============================================================

INSERT INTO public.property_integration_status
  (property_id, integration_name, category, status, last_sync_at, daily_api_calls, daily_api_limit) VALUES

-- Maple Heights (596d3791) — all 5 connected (READY)
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','apartments_com','lead_sources','connected',now()-interval '1 hour',312,1000),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','zillow','lead_sources','connected',now()-interval '2 hours',278,1000),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','rent_com','lead_sources','connected',now()-interval '1 day',189,1000),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','appfolio','property_management','connected',now()-interval '1 hour',445,1000),
('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','yardi','property_management','connected',now()-interval '2 hours',367,1000),

-- Cedar Point Apartments (92e9be2c) — all 5 connected (READY)
('92e9be2c-05e0-4bcc-a646-895ae83dd515','apartments_com','lead_sources','connected',now()-interval '30 minutes',847,1000),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','zillow','lead_sources','connected',now()-interval '1 hour',512,1000),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','rent_com','lead_sources','connected',now()-interval '2 hours',398,1000),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','appfolio','property_management','connected',now()-interval '30 minutes',621,1000),
('92e9be2c-05e0-4bcc-a646-895ae83dd515','yardi','property_management','connected',now()-interval '1 hour',435,1000),

-- The Meridian (a8d0cd37) — all 5 connected (READY)
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','apartments_com','lead_sources','connected',now()-interval '45 minutes',567,1000),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','zillow','lead_sources','connected',now()-interval '90 minutes',423,1000),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','rent_com','lead_sources','connected',now()-interval '3 hours',312,1000),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','appfolio','property_management','connected',now()-interval '1 hour',689,1000),
('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','yardi','property_management','connected',now()-interval '2 hours',534,1000),

-- Lakeside Commons (ec6e19d8) — all 5 connected (READY)
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','apartments_com','lead_sources','connected',now()-interval '1 hour',445,1000),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','zillow','lead_sources','connected',now()-interval '2 hours',356,1000),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','rent_com','lead_sources','connected',now()-interval '4 hours',234,1000),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','appfolio','property_management','connected',now()-interval '1 hour',512,1000),
('ec6e19d8-ccee-47bb-9866-13db48ecb8e5','yardi','property_management','connected',now()-interval '3 hours',389,1000),

-- Highland Square (f48c0983) — all 5 connected (READY)
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','apartments_com','lead_sources','connected',now()-interval '2 hours',378,1000),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','zillow','lead_sources','connected',now()-interval '3 hours',289,1000),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','rent_com','lead_sources','connected',now()-interval '1 day',178,1000),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','appfolio','property_management','connected',now()-interval '1 hour',456,1000),
('f48c0983-006e-4cfa-b0bd-18896b5c6d00','yardi','property_management','connected',now()-interval '2 hours',334,1000),

-- Beacon Hill Towers (ffe230e2) — all 5 connected (READY)
('ffe230e2-6caf-464c-9568-4aab4f8fb046','apartments_com','lead_sources','connected',now()-interval '1 hour',523,1000),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','zillow','lead_sources','connected',now()-interval '2 hours',412,1000),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','rent_com','lead_sources','connected',now()-interval '3 hours',298,1000),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','appfolio','property_management','connected',now()-interval '45 minutes',634,1000),
('ffe230e2-6caf-464c-9568-4aab4f8fb046','yardi','property_management','connected',now()-interval '1 hour',489,1000),

-- River Lofts (c5a7fd3a) — 4 connected, Yardi missing (BLOCKED)
('c5a7fd3a-71be-4895-995f-3700922467d5','apartments_com','lead_sources','connected',now()-interval '2 hours',245,1000),
('c5a7fd3a-71be-4895-995f-3700922467d5','zillow','lead_sources','connected',now()-interval '4 hours',182,1000),
('c5a7fd3a-71be-4895-995f-3700922467d5','rent_com','lead_sources','connected',now()-interval '1 day',98,1000),
('c5a7fd3a-71be-4895-995f-3700922467d5','appfolio','property_management','connected',now()-interval '1 hour',320,1000),
('c5a7fd3a-71be-4895-995f-3700922467d5','yardi','property_management','not_connected',NULL,0,1000),

-- Sunset Ridge (39d2e354) — 2 connected (BLOCKED)
('39d2e354-9052-4eec-8bbf-0e39948c21ca','apartments_com','lead_sources','connected',now()-interval '3 hours',134,1000),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','zillow','lead_sources','connected',now()-interval '4 hours',98,1000),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','rent_com','lead_sources','not_connected',NULL,0,1000),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','appfolio','property_management','not_connected',NULL,0,1000),
('39d2e354-9052-4eec-8bbf-0e39948c21ca','yardi','property_management','not_connected',NULL,0,1000),

-- Brookstone Flats (92edec9c) — 3 connected (BLOCKED)
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','apartments_com','lead_sources','connected',now()-interval '2 hours',289,1000),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','zillow','lead_sources','connected',now()-interval '3 hours',201,1000),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','rent_com','lead_sources','not_connected',NULL,0,1000),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','appfolio','property_management','connected',now()-interval '5 hours',178,1000),
('92edec9c-fa8e-4945-88f4-9c9eeaab71bb','yardi','property_management','not_connected',NULL,0,1000),

-- Parkside Estates (e6e0e36b) — 3 connected (BLOCKED)
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','apartments_com','lead_sources','connected',now()-interval '1 day',134,1000),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','zillow','lead_sources','connected',now()-interval '1 day',98,1000),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','rent_com','lead_sources','not_connected',NULL,0,1000),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','appfolio','property_management','connected',now()-interval '3 hours',256,1000),
('e6e0e36b-dd01-49e1-99c3-bafde02b5e0e','yardi','property_management','not_connected',NULL,0,1000),

-- Aurora Place (0a39dc44) — 1 connected (BLOCKED)
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','apartments_com','lead_sources','connected',now()-interval '2 days',45,1000),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','zillow','lead_sources','not_connected',NULL,0,1000),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','rent_com','lead_sources','not_connected',NULL,0,1000),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','appfolio','property_management','not_connected',NULL,0,1000),
('0a39dc44-b1d6-4c45-9e11-96c6476104e5','yardi','property_management','not_connected',NULL,0,1000),

-- Grand Central Living (183f7339) — 3 connected (IN-PROGRESS)
('183f7339-e6c7-4d08-9299-422207e91f29','apartments_com','lead_sources','connected',now()-interval '1 hour',267,1000),
('183f7339-e6c7-4d08-9299-422207e91f29','zillow','lead_sources','connected',now()-interval '2 hours',198,1000),
('183f7339-e6c7-4d08-9299-422207e91f29','rent_com','lead_sources','connected',now()-interval '1 day',145,1000),
('183f7339-e6c7-4d08-9299-422207e91f29','appfolio','property_management','not_connected',NULL,0,1000),
('183f7339-e6c7-4d08-9299-422207e91f29','yardi','property_management','not_connected',NULL,0,1000),

-- Skyline Towers (e3ff8f2a) — 4 connected (IN-PROGRESS)
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','apartments_com','lead_sources','connected',now()-interval '1 hour',389,1000),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','zillow','lead_sources','connected',now()-interval '2 hours',312,1000),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','rent_com','lead_sources','connected',now()-interval '3 hours',234,1000),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','appfolio','property_management','connected',now()-interval '1 hour',456,1000),
('e3ff8f2a-9d13-46b6-8673-3d99fa5cf949','yardi','property_management','not_connected',NULL,0,1000),

-- Pine Grove Villas (f7c028a9) — 4 connected (IN-PROGRESS)
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','apartments_com','lead_sources','connected',now()-interval '2 hours',312,1000),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','zillow','lead_sources','connected',now()-interval '3 hours',245,1000),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','rent_com','lead_sources','connected',now()-interval '1 day',178,1000),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','appfolio','property_management','connected',now()-interval '2 hours',389,1000),
('f7c028a9-af8c-4f60-9a48-467ca4668cfb','yardi','property_management','not_connected',NULL,0,1000),

-- Cityline Residences (fc705241) — 4 connected (IN-PROGRESS)
('fc705241-30eb-448d-b3a8-416117044176','apartments_com','lead_sources','connected',now()-interval '1 hour',423,1000),
('fc705241-30eb-448d-b3a8-416117044176','zillow','lead_sources','connected',now()-interval '2 hours',334,1000),
('fc705241-30eb-448d-b3a8-416117044176','rent_com','lead_sources','connected',now()-interval '4 hours',212,1000),
('fc705241-30eb-448d-b3a8-416117044176','appfolio','property_management','connected',now()-interval '1 hour',512,1000),
('fc705241-30eb-448d-b3a8-416117044176','yardi','property_management','not_connected',NULL,0,1000),

-- Elmwood Court (fe7c0806) — 4 connected (IN-PROGRESS)
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','apartments_com','lead_sources','connected',now()-interval '3 hours',289,1000),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','zillow','lead_sources','connected',now()-interval '4 hours',223,1000),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','rent_com','lead_sources','connected',now()-interval '1 day',156,1000),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','appfolio','property_management','connected',now()-interval '2 hours',345,1000),
('fe7c0806-df39-4aa4-8cb5-5fd44975a66e','yardi','property_management','not_connected',NULL,0,1000)

ON CONFLICT (property_id, integration_name) DO UPDATE SET
  status          = EXCLUDED.status,
  last_sync_at    = EXCLUDED.last_sync_at,
  daily_api_calls = EXCLUDED.daily_api_calls,
  updated_at      = now();


-- ============================================================
-- SECTION 8 — property_ai_content_jobs
-- Sample job history: completed, pending, failed
-- ============================================================

INSERT INTO public.property_ai_content_jobs
  (property_id, section, content_type, status, prompt_used,
   generated_content, triggered_by, created_at, completed_at) VALUES

('596d3791-eb69-4030-9e1b-2e3f9b2ddd09','content_faqs','faq','completed',
 'Generate pet policy FAQ for Maple Heights demo property CA',
 '{"question":"What is the pet policy?","answer":"Cats and dogs welcome, maximum 2 pets up to 60 lbs."}',
 'admin', now()-interval '5 days', now()-interval '5 days' + interval '9 seconds'),

('92e9be2c-05e0-4bcc-a646-895ae83dd515','content_faqs','faq','completed',
 'Generate lease break policy FAQ for Cedar Point Apartments demo property CA',
 '{"question":"What is the lease break policy?","answer":"Early termination requires 60-day notice and fee of 2 months rent."}',
 'admin', now()-interval '3 days', now()-interval '3 days' + interval '7 seconds'),

('a8d0cd37-5a6e-4a9d-b97e-0e74432a5fc6','amenities','amenity_description','completed',
 'Generate descriptions for gym and pool amenities at The Meridian',
 '{"amenities_updated":2}',
 'admin', now()-interval '8 days', now()-interval '8 days' + interval '12 seconds'),

('c5a7fd3a-71be-4895-995f-3700922467d5','content_faqs','faq','pending',
 NULL, NULL,
 'admin', now()-interval '5 minutes', NULL),

('0a39dc44-b1d6-4c45-9e11-96c6476104e5','content_faqs','faq','failed',
 'Generate missing FAQs for Aurora Place demo property',
 NULL,
 'admin', now()-interval '1 day', now()-interval '1 day' + interval '30 seconds')

ON CONFLICT DO NOTHING;

UPDATE public.property_ai_content_jobs
SET error_message = 'LLM API timeout after 30 seconds. Please try again.'
WHERE property_id = '0a39dc44-b1d6-4c45-9e11-96c6476104e5'
  AND status = 'failed';


-- ============================================================
-- FINAL SUMMARY
-- ============================================================
DO $$
BEGIN
  RAISE NOTICE '✅ Seed complete! Real property IDs used throughout.';
  RAISE NOTICE '   unit_images:    ~50 rows';
  RAISE NOTICE '   sections:       96 rows (6 × 16 properties)';
  RAISE NOTICE '   status:         16 rows (via recalculate_onboarding_status)';
  RAISE NOTICE '   blockers:       15 rows (4 blocking, 11 warnings)';
  RAISE NOTICE '   faqs:           ~130 rows (published + empty placeholders)';
  RAISE NOTICE '   amenities:      ~32 rows';
  RAISE NOTICE '   integrations:   80 rows (5 × 16 properties)';
  RAISE NOTICE '   ai_jobs:        5 rows';
  RAISE NOTICE '';
  RAISE NOTICE '   Status breakdown:';
  RAISE NOTICE '   READY (5):       Maple Heights, Cedar Point, The Meridian, Lakeside Commons, Highland Square, Beacon Hill Towers';
  RAISE NOTICE '   BLOCKED (4):     Aurora Place, Sunset Ridge, Brookstone Flats, River Lofts, Parkside Estates';
  RAISE NOTICE '   IN-PROGRESS (7): Grand Central, Skyline Towers, Pine Grove, Cityline, Elmwood Court';
END $$;
