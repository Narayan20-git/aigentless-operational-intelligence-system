-- ============================================================
-- Aigentless POC — Complete Seed Data
-- Category 1: properties, floorplans, units,
--             property_images, unit_images
-- Category 2: 7 new onboarding tables
-- 20+ records per table | Matches Figma exactly
-- Run AFTER migration_category2.sql
-- ============================================================

-- ============================================================
-- CATEGORY 1 — SEED DATA (strict schema from sql_dump_karan)
-- ============================================================

-- Property IDs (fixed UUIDs for cross-table references)
-- Using fixed UUIDs so seed can be re-run safely
DO $$ BEGIN
  RAISE NOTICE 'Seeding Category 1 tables...';
END $$;

-- ── PROPERTIES ──────────────────────────────────────────────
INSERT INTO public.properties (
  id, name, description, address, latitude, longitude,
  units, floors, year_built, website, amenities,
  housing_type, go_live_date, internal_only,
  payment_model, utilities, fees,
  hide_price, hide_fees, hide_parking_price,
  created_at
) VALUES
(
  'a1000000-0000-0000-0000-000000000001',
  'River Lofts',
  'Modern loft-style apartments along the river walk with stunning views and premium finishes.',
  '{"street": "1450 River Walk Blvd", "city": "Austin", "state": "TX", "zip": "78701"}',
  30.2672, -97.7431, 48, 6, 2019,
  'https://riverlofts.com',
  ARRAY['Pool','Gym','Rooftop Deck','Pet Spa','Co-working Space','EV Charging','Package Lockers','Bike Storage','Guest Suite','Movie Lounge','BBQ Area','Dog Park','Concierge','Valet Parking','Storage Units','Yoga Studio','Coffee Bar','Sky Lounge'],
  'multifamily', NULL, false,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '30 days'
),
(
  'a1000000-0000-0000-0000-000000000002',
  'Parkside Commons',
  'Community-focused apartments adjacent to Parkside Nature Reserve.',
  '{"street": "820 Parkside Drive", "city": "Austin", "state": "TX", "zip": "78704"}',
  30.2500, -97.7700, 72, 4, 2015,
  'https://parksidecommons.com',
  ARRAY['Pool','Gym','Rooftop Terrace','Pet Spa','Co-working Space','EV Charging','Package Lockers','Bike Storage','Guest Suite','Movie Lounge','BBQ Area','Dog Park','Playground','Car Wash','Fitness Studio'],
  'multifamily', NULL, false,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '20 days'
),
(
  'a1000000-0000-0000-0000-000000000003',
  'Skyline Towers',
  'Luxury high-rise living in the heart of downtown Austin with panoramic skyline views.',
  '{"street": "300 Skyline Plaza", "city": "Austin", "state": "TX", "zip": "78703"}',
  30.2680, -97.7400, 120, 24, 2021,
  'https://skylinetowers.com',
  ARRAY['Pool','Gym','Rooftop Lounge','Pet Spa','Co-working Space','EV Charging','Package Lockers','Bike Storage','Guest Suite','Theater Room','BBQ Area','Dog Park','Concierge','Valet Parking','Storage Units','Yoga Studio','Coffee Bar','Sky Lounge','Wine Cellar','Business Center','Shuttle Service','Smart Home Tech','24hr Security','Spa'],
  'high-rise', (now() - interval '10 days')::date, false,
  'Subscription', '{"water": true, "trash": true, "gas": false}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '45 days'
),
(
  'a1000000-0000-0000-0000-000000000004',
  'Northgate Apartments',
  NULL,
  '{"street": "510 Northgate Road", "city": "Austin", "state": "TX", "zip": "78752"}',
  30.3200, -97.7200, 36, 3, 2010,
  '',
  ARRAY['Pool','Gym','Laundry Room','Parking','Storage','BBQ Area','Playground','Bike Rack','Package Room','Dog Walk Area'],
  'multifamily', NULL, true,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '10 days'
),
(
  'a1000000-0000-0000-0000-000000000005',
  'Maple Heights',
  'Boutique mid-rise apartments surrounded by mature maple trees in a quiet neighborhood.',
  '{"street": "215 Maple Heights Blvd", "city": "Austin", "state": "TX", "zip": "78705"}',
  30.2900, -97.7350, 60, 5, 2018,
  'https://mapleheights.com',
  ARRAY['Pool','Gym','Courtyard','Pet Spa','Package Lockers','Bike Storage','BBQ Area','Dog Park','Rooftop Deck','Co-working Space','EV Charging','Coffee Bar','Yoga Studio','Storage Units','Car Wash','Shuttle Service','Smart Home Tech','24hr Security','Spa','Wine Cellar'],
  'multifamily', (now() - interval '20 days')::date, false,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '60 days'
),
(
  'a1000000-0000-0000-0000-000000000006',
  'Oak Residences',
  'Charming townhouse-style residences nestled among old-growth oak trees.',
  '{"street": "780 Oak Street", "city": "Austin", "state": "TX", "zip": "78745"}',
  30.2200, -97.7800, 28, 2, 2012,
  'https://oakresidences.com',
  ARRAY['Dog Park','Bike Rack','Package Room','Storage Units','Car Wash','Fitness Studio','Yoga Room','Courtyard','BBQ Area','Playground','EV Charging','Laundry','Pool','Gym'],
  'townhouse', NULL, false,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '15 days'
),
(
  'a1000000-0000-0000-0000-000000000007',
  'Cedar Grove',
  'Upscale apartment living with resort-style amenities in Cedar Grove neighborhood.',
  '{"street": "1100 Cedar Grove Lane", "city": "Austin", "state": "TX", "zip": "78748"}',
  30.1800, -97.8200, 54, 5, 2017,
  'https://cedargrove.com',
  ARRAY['Pool','Gym','Rooftop Deck','Concierge Service','Valet Parking','Pet Spa','Co-working Space','EV Charging','Package Lockers','Bike Storage','Guest Suite','Movie Lounge','BBQ Area','Dog Park','Wine Cellar','Business Center'],
  'multifamily', NULL, false,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '25 days'
),
(
  'a1000000-0000-0000-0000-000000000008',
  'Summit Place',
  NULL,
  '{"street": "990 Summit Drive", "city": "Austin", "state": "TX", "zip": "78759"}',
  30.4000, -97.7500, 42, 4, 2008,
  '',
  ARRAY['Pool','Gym','Laundry','Parking','BBQ Area','Playground','Storage','Bike Rack'],
  'multifamily', NULL, true,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '7 days'
),
(
  'a1000000-0000-0000-0000-000000000009',
  'Harbor View',
  'Premium high-rise living with sweeping harbor views and world-class amenities.',
  '{"street": "400 Harbor View Court", "city": "Austin", "state": "TX", "zip": "78730"}',
  30.3800, -97.8500, 96, 18, 2022,
  'https://harborview.com',
  ARRAY['Pool','Gym','Rooftop Lounge','Pet Spa','Co-working Space','EV Charging','Package Lockers','Bike Storage','Guest Suite','Theater Room','BBQ Area','Dog Park','Concierge','Valet Parking','Storage Units','Yoga Studio','Coffee Bar','Sky Lounge','Wine Cellar','Business Center','Shuttle Service','Smart Home Tech','24hr Security','Spa','Paddle Courts','Golf Simulator','Kids Club'],
  'high-rise', (now() - interval '5 days')::date, false,
  'Subscription', '{"water": true, "trash": true, "gas": false}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '50 days'
),
(
  'a1000000-0000-0000-0000-000000000010',
  'Westfield Court',
  'Contemporary apartment living in the vibrant Westfield district.',
  '{"street": "650 Westfield Court Ave", "city": "Austin", "state": "TX", "zip": "78750"}',
  30.4200, -97.7900, 80, 7, 2020,
  'https://westfieldcourt.com',
  ARRAY['Pool','Gym','Rooftop Deck','Pet Spa','Co-working Space','EV Charging','Package Lockers','Bike Storage','Guest Suite','Movie Lounge','BBQ Area','Dog Park','Concierge','Storage Units','Yoga Studio','Coffee Bar','Sky Lounge','Wine Cellar','Business Center','Shuttle Service','Smart Home Tech','24hr Security'],
  'multifamily', NULL, false,
  'Subscription', '{"water": true, "trash": true}', ARRAY[]::jsonb[],
  'false', false, false,
  now() - interval '35 days'
)
ON CONFLICT (id) DO UPDATE SET
  name        = EXCLUDED.name,
  description = EXCLUDED.description;

-- ── FLOORPLANS ───────────────────────────────────────────────
INSERT INTO public.floorplans (
  id, property_id, name, description,
  bedrooms, bathrooms, square_footage,
  pets_allowed, amenities, created_at
) VALUES
('b1000000-0000-0000-0000-000000000001','a1000000-0000-0000-0000-000000000001','Studio Loft','Modern studio with open layout',0,1,520,true,ARRAY['Stainless Appliances','Hardwood Floors','City View'],now()-interval '30 days'),
('b1000000-0000-0000-0000-000000000002','a1000000-0000-0000-0000-000000000001','1BR River View','One bedroom with river views',1,1,750,true,ARRAY['River View','Balcony','W/D In Unit'],now()-interval '30 days'),
('b1000000-0000-0000-0000-000000000003','a1000000-0000-0000-0000-000000000001','2BR Loft','Spacious two bedroom loft',2,2,1100,true,ARRAY['Open Floor Plan','City View','Balcony'],now()-interval '30 days'),
('b1000000-0000-0000-0000-000000000004','a1000000-0000-0000-0000-000000000001','3BR Penthouse','Luxury penthouse unit',3,2,1650,true,ARRAY['Penthouse','Panoramic View','Private Terrace'],now()-interval '30 days'),
('b1000000-0000-0000-0000-000000000005','a1000000-0000-0000-0000-000000000002','1BR Parkside','One bedroom with park views',1,1,720,true,ARRAY['Park View','Patio','Stainless Appliances'],now()-interval '20 days'),
('b1000000-0000-0000-0000-000000000006','a1000000-0000-0000-0000-000000000002','2BR Parkside','Two bedroom with balcony',2,2,1050,true,ARRAY['Park View','Balcony','W/D In Unit'],now()-interval '20 days'),
('b1000000-0000-0000-0000-000000000007','a1000000-0000-0000-0000-000000000003','1BR Skyline','Floor-to-ceiling windows',1,1,800,true,ARRAY['Floor-to-Ceiling Windows','Smart Home','City View'],now()-interval '45 days'),
('b1000000-0000-0000-0000-000000000008','a1000000-0000-0000-0000-000000000003','2BR Skyline','Corner unit with double balcony',2,2,1200,true,ARRAY['Corner Unit','Double Balcony','Premium Appliances'],now()-interval '45 days'),
('b1000000-0000-0000-0000-000000000009','a1000000-0000-0000-0000-000000000003','3BR Penthouse','Private rooftop penthouse',3,3,2100,false,ARRAY['Private Rooftop','Butler Kitchen','Panoramic Views'],now()-interval '45 days'),
('b1000000-0000-0000-0000-000000000010','a1000000-0000-0000-0000-000000000004','1BR Standard','Standard one bedroom unit',1,1,650,false,ARRAY['Carpet','Basic Appliances'],now()-interval '10 days'),
('b1000000-0000-0000-0000-000000000011','a1000000-0000-0000-0000-000000000005','1BR Maple','Modern one bedroom',1,1,710,true,ARRAY['Tree View','Modern Finishes','W/D In Unit'],now()-interval '60 days'),
('b1000000-0000-0000-0000-000000000012','a1000000-0000-0000-0000-000000000005','2BR Maple','Two bedroom with balcony',2,2,1080,true,ARRAY['Balcony','Modern Kitchen','Walk-in Closet'],now()-interval '60 days'),
('b1000000-0000-0000-0000-000000000013','a1000000-0000-0000-0000-000000000006','2BR Townhouse','Private patio townhouse',2,2,1300,true,ARRAY['Private Patio','Attached Garage','Hardwood Floors'],now()-interval '15 days'),
('b1000000-0000-0000-0000-000000000014','a1000000-0000-0000-0000-000000000007','1BR Cedar','Modern one bedroom',1,1,760,true,ARRAY['City View','Modern Kitchen','W/D In Unit'],now()-interval '25 days'),
('b1000000-0000-0000-0000-000000000015','a1000000-0000-0000-0000-000000000007','2BR Cedar','Spacious two bedroom',2,2,1150,true,ARRAY['Balcony','Premium Finishes','Walk-in Closet'],now()-interval '25 days'),
('b1000000-0000-0000-0000-000000000016','a1000000-0000-0000-0000-000000000008','1BR Summit','Standard one bedroom',1,1,680,false,ARRAY['Basic Appliances','Carpet'],now()-interval '7 days'),
('b1000000-0000-0000-0000-000000000017','a1000000-0000-0000-0000-000000000009','1BR Harbor','Premium one bedroom',1,1,820,true,ARRAY['Ocean View','Smart Home','Premium Finishes'],now()-interval '50 days'),
('b1000000-0000-0000-0000-000000000018','a1000000-0000-0000-0000-000000000009','2BR Harbor','Luxury two bedroom',2,2,1350,true,ARRAY['Corner Unit','Panoramic View','Butler Kitchen'],now()-interval '50 days'),
('b1000000-0000-0000-0000-000000000019','a1000000-0000-0000-0000-000000000010','1BR Westfield','Contemporary one bedroom',1,1,790,true,ARRAY['Modern Finishes','Smart Home','City View'],now()-interval '35 days'),
('b1000000-0000-0000-0000-000000000020','a1000000-0000-0000-0000-000000000010','2BR Westfield','Spacious two bedroom',2,2,1180,true,ARRAY['Balcony','Open Kitchen','Walk-in Closet'],now()-interval '35 days')
ON CONFLICT (id) DO NOTHING;

-- ── UNITS ────────────────────────────────────────────────────
INSERT INTO public.units (
  id, property_id, floorplan_id, unit, floor,
  monthly_rent, active, tourable, rentable,
  pets_allowed, created_at
) VALUES
-- River Lofts units
('c1000000-0000-0000-0000-000000000001','a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000001','1A','1',1800,true,true,true,true,now()-interval '30 days'),
('c1000000-0000-0000-0000-000000000002','a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000002','2B','2',2200,true,true,true,true,now()-interval '30 days'),
('c1000000-0000-0000-0000-000000000003','a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000002','3B','3',2250,true,true,true,true,now()-interval '30 days'),
('c1000000-0000-0000-0000-000000000004','a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000003','4C','4',2900,true,true,true,true,now()-interval '30 days'),
('c1000000-0000-0000-0000-000000000005','a1000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000004','5D','5',4200,true,true,true,true,now()-interval '30 days'),
-- Parkside Commons units
('c1000000-0000-0000-0000-000000000006','a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000005','1A','1',1950,true,true,true,true,now()-interval '20 days'),
('c1000000-0000-0000-0000-000000000007','a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000005','1C','1',1975,true,true,true,true,now()-interval '20 days'),
('c1000000-0000-0000-0000-000000000008','a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000006','2B','2',2600,true,true,true,true,now()-interval '20 days'),
('c1000000-0000-0000-0000-000000000009','a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000006','3A','3',2650,true,true,true,true,now()-interval '20 days'),
('c1000000-0000-0000-0000-000000000010','a1000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000005','4B','4',2000,true,true,true,true,now()-interval '20 days'),
-- Skyline Towers units
('c1000000-0000-0000-0000-000000000011','a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000007','1A','1',3200,true,true,true,true,now()-interval '45 days'),
('c1000000-0000-0000-0000-000000000012','a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000008','2B','2',4500,true,true,true,true,now()-interval '45 days'),
('c1000000-0000-0000-0000-000000000013','a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000009','3C','3',7200,true,true,true,false,now()-interval '45 days'),
('c1000000-0000-0000-0000-000000000014','a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000007','4D','4',3400,true,true,true,true,now()-interval '45 days'),
('c1000000-0000-0000-0000-000000000015','a1000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000008','8D','8',7500,true,true,true,true,now()-interval '45 days'),
-- Northgate (inactive - not set up yet)
('c1000000-0000-0000-0000-000000000016','a1000000-0000-0000-0000-000000000004','b1000000-0000-0000-0000-000000000010','1A','1',1200,false,false,false,false,now()-interval '10 days'),
('c1000000-0000-0000-0000-000000000017','a1000000-0000-0000-0000-000000000004','b1000000-0000-0000-0000-000000000010','1B','1',1200,false,false,false,false,now()-interval '10 days'),
-- Maple Heights units
('c1000000-0000-0000-0000-000000000018','a1000000-0000-0000-0000-000000000005','b1000000-0000-0000-0000-000000000011','1A','1',2100,true,true,true,true,now()-interval '60 days'),
('c1000000-0000-0000-0000-000000000019','a1000000-0000-0000-0000-000000000005','b1000000-0000-0000-0000-000000000012','2B','2',2800,true,true,true,true,now()-interval '60 days'),
('c1000000-0000-0000-0000-000000000020','a1000000-0000-0000-0000-000000000005','b1000000-0000-0000-0000-000000000011','3C','3',2150,true,true,true,true,now()-interval '60 days'),
-- Oak Residences
('c1000000-0000-0000-0000-000000000021','a1000000-0000-0000-0000-000000000006','b1000000-0000-0000-0000-000000000013','1A','1',2500,true,true,true,true,now()-interval '15 days'),
('c1000000-0000-0000-0000-000000000022','a1000000-0000-0000-0000-000000000006','b1000000-0000-0000-0000-000000000013','2B','1',2550,true,true,true,true,now()-interval '15 days'),
-- Cedar Grove
('c1000000-0000-0000-0000-000000000023','a1000000-0000-0000-0000-000000000007','b1000000-0000-0000-0000-000000000014','1A','1',2400,true,true,true,true,now()-interval '25 days'),
('c1000000-0000-0000-0000-000000000024','a1000000-0000-0000-0000-000000000007','b1000000-0000-0000-0000-000000000015','2B','2',3200,true,true,true,true,now()-interval '25 days'),
-- Harbor View
('c1000000-0000-0000-0000-000000000025','a1000000-0000-0000-0000-000000000009','b1000000-0000-0000-0000-000000000017','1A','1',3800,true,true,true,true,now()-interval '50 days'),
('c1000000-0000-0000-0000-000000000026','a1000000-0000-0000-0000-000000000009','b1000000-0000-0000-0000-000000000018','2B','2',5500,true,true,true,true,now()-interval '50 days'),
-- Westfield Court
('c1000000-0000-0000-0000-000000000027','a1000000-0000-0000-0000-000000000010','b1000000-0000-0000-0000-000000000019','1A','1',2600,true,true,true,true,now()-interval '35 days'),
('c1000000-0000-0000-0000-000000000028','a1000000-0000-0000-0000-000000000010','b1000000-0000-0000-0000-000000000020','2B','2',3400,true,true,true,true,now()-interval '35 days'),
-- Summit Place
('c1000000-0000-0000-0000-000000000029','a1000000-0000-0000-0000-000000000008','b1000000-0000-0000-0000-000000000016','1A','1',1600,false,false,false,false,now()-interval '7 days'),
('c1000000-0000-0000-0000-000000000030','a1000000-0000-0000-0000-000000000008','b1000000-0000-0000-0000-000000000016','1B','1',1650,false,false,false,false,now()-interval '7 days')
ON CONFLICT (id) DO NOTHING;

-- ── PROPERTY IMAGES ──────────────────────────────────────────
INSERT INTO public.property_images (property_id, image_index, image_path, created_at) VALUES
('a1000000-0000-0000-0000-000000000001',1,'properties/river-lofts/exterior_01.jpg',now()-interval '29 days'),
('a1000000-0000-0000-0000-000000000001',2,'properties/river-lofts/lobby_01.jpg',now()-interval '29 days'),
('a1000000-0000-0000-0000-000000000001',3,'properties/river-lofts/pool_01.jpg',now()-interval '29 days'),
('a1000000-0000-0000-0000-000000000001',4,'properties/river-lofts/gym_01.jpg',now()-interval '29 days'),
('a1000000-0000-0000-0000-000000000001',5,'properties/river-lofts/rooftop_01.jpg',now()-interval '29 days'),
('a1000000-0000-0000-0000-000000000002',1,'properties/parkside/exterior_01.jpg',now()-interval '19 days'),
('a1000000-0000-0000-0000-000000000002',2,'properties/parkside/lobby_01.jpg',now()-interval '19 days'),
('a1000000-0000-0000-0000-000000000002',3,'properties/parkside/pool_01.jpg',now()-interval '19 days'),
('a1000000-0000-0000-0000-000000000003',1,'properties/skyline/exterior_01.jpg',now()-interval '44 days'),
('a1000000-0000-0000-0000-000000000003',2,'properties/skyline/lobby_01.jpg',now()-interval '44 days'),
('a1000000-0000-0000-0000-000000000003',3,'properties/skyline/pool_01.jpg',now()-interval '44 days'),
('a1000000-0000-0000-0000-000000000003',4,'properties/skyline/gym_01.jpg',now()-interval '44 days'),
('a1000000-0000-0000-0000-000000000003',5,'properties/skyline/rooftop_01.jpg',now()-interval '44 days'),
('a1000000-0000-0000-0000-000000000003',6,'properties/skyline/amenities_01.jpg',now()-interval '44 days'),
('a1000000-0000-0000-0000-000000000005',1,'properties/maple/exterior_01.jpg',now()-interval '59 days'),
('a1000000-0000-0000-0000-000000000005',2,'properties/maple/lobby_01.jpg',now()-interval '59 days'),
('a1000000-0000-0000-0000-000000000005',3,'properties/maple/pool_01.jpg',now()-interval '59 days'),
('a1000000-0000-0000-0000-000000000005',4,'properties/maple/gym_01.jpg',now()-interval '59 days'),
('a1000000-0000-0000-0000-000000000009',1,'properties/harbor/exterior_01.jpg',now()-interval '49 days'),
('a1000000-0000-0000-0000-000000000009',2,'properties/harbor/lobby_01.jpg',now()-interval '49 days'),
('a1000000-0000-0000-0000-000000000009',3,'properties/harbor/pool_01.jpg',now()-interval '49 days'),
('a1000000-0000-0000-0000-000000000009',4,'properties/harbor/amenities_01.jpg',now()-interval '49 days')
ON CONFLICT DO NOTHING;

-- ── UNIT IMAGES ──────────────────────────────────────────────
INSERT INTO public.unit_images (unit_id, image_index, image_path, created_at) VALUES
-- River Lofts (3B and 7A have no photos — intentional blocker)
('c1000000-0000-0000-0000-000000000001',1,'units/river-lofts/1A/living_01.jpg',now()-interval '28 days'),
('c1000000-0000-0000-0000-000000000001',2,'units/river-lofts/1A/bedroom_01.jpg',now()-interval '28 days'),
('c1000000-0000-0000-0000-000000000002',1,'units/river-lofts/2B/living_01.jpg',now()-interval '28 days'),
('c1000000-0000-0000-0000-000000000002',2,'units/river-lofts/2B/bedroom_01.jpg',now()-interval '28 days'),
('c1000000-0000-0000-0000-000000000004',1,'units/river-lofts/4C/living_01.jpg',now()-interval '28 days'),
('c1000000-0000-0000-0000-000000000004',2,'units/river-lofts/4C/bedroom_01.jpg',now()-interval '28 days'),
-- Skyline Towers (all have photos)
('c1000000-0000-0000-0000-000000000011',1,'units/skyline/1A/living_01.jpg',now()-interval '43 days'),
('c1000000-0000-0000-0000-000000000011',2,'units/skyline/1A/bedroom_01.jpg',now()-interval '43 days'),
('c1000000-0000-0000-0000-000000000012',1,'units/skyline/2B/living_01.jpg',now()-interval '43 days'),
('c1000000-0000-0000-0000-000000000012',2,'units/skyline/2B/bedroom_01.jpg',now()-interval '43 days'),
('c1000000-0000-0000-0000-000000000013',1,'units/skyline/3C/living_01.jpg',now()-interval '43 days'),
('c1000000-0000-0000-0000-000000000013',2,'units/skyline/3C/bedroom_01.jpg',now()-interval '43 days'),
-- Maple Heights
('c1000000-0000-0000-0000-000000000018',1,'units/maple/1A/living_01.jpg',now()-interval '58 days'),
('c1000000-0000-0000-0000-000000000018',2,'units/maple/1A/bedroom_01.jpg',now()-interval '58 days'),
('c1000000-0000-0000-0000-000000000019',1,'units/maple/2B/living_01.jpg',now()-interval '58 days'),
('c1000000-0000-0000-0000-000000000019',2,'units/maple/2B/bedroom_01.jpg',now()-interval '58 days'),
-- Harbor View
('c1000000-0000-0000-0000-000000000025',1,'units/harbor/1A/living_01.jpg',now()-interval '48 days'),
('c1000000-0000-0000-0000-000000000025',2,'units/harbor/1A/bedroom_01.jpg',now()-interval '48 days'),
('c1000000-0000-0000-0000-000000000026',1,'units/harbor/2B/living_01.jpg',now()-interval '48 days'),
('c1000000-0000-0000-0000-000000000026',2,'units/harbor/2B/bedroom_01.jpg',now()-interval '48 days'),
-- Westfield Court
('c1000000-0000-0000-0000-000000000027',1,'units/westfield/1A/living_01.jpg',now()-interval '33 days'),
('c1000000-0000-0000-0000-000000000027',2,'units/westfield/1A/bedroom_01.jpg',now()-interval '33 days')
ON CONFLICT DO NOTHING;

-- ============================================================
-- CATEGORY 2 — SEED DATA (7 new onboarding tables)
-- ============================================================
DO $$ BEGIN
  RAISE NOTICE 'Seeding Category 2 tables...';
END $$;

-- ── PROPERTY ONBOARDING SECTIONS ────────────────────────────
INSERT INTO public.property_onboarding_sections
  (property_id, section, completion_pct, status, metadata) VALUES

-- River Lofts (92% avg — blocked)
('a1000000-0000-0000-0000-000000000001','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000001','units_floor_plans',100,'complete',    '{"units_added":48,"floor_plans":6}'),
('a1000000-0000-0000-0000-000000000001','amenities',        100,'complete',    '{"amenities_count":18,"described":18}'),
('a1000000-0000-0000-0000-000000000001','media_photos',      95,'in-progress', '{"uploaded":57,"required":60,"missing":["Unit 3B","Unit 7A"]}'),
('a1000000-0000-0000-0000-000000000001','content_faqs',      75,'blocked',     '{"completed":9,"total":12,"missing":["Pet policy FAQ","Parking FAQ","Lease break policy"]}'),
('a1000000-0000-0000-0000-000000000001','integrations',      80,'in-progress', '{"connected":4,"required":5,"pending":["Yardi Voyager PMS sync"]}'),

-- Parkside Commons (68% avg — in-progress)
('a1000000-0000-0000-0000-000000000002','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000002','units_floor_plans', 85,'in-progress', '{"units_added":72,"floor_plans":4,"missing_units":["2A","4C","6B","8D","10A","12C","14B","16F"]}'),
('a1000000-0000-0000-0000-000000000002','amenities',         60,'in-progress', '{"amenities_count":20,"described":12,"incomplete":["Rooftop terrace","Pet spa","Co-working space"]}'),
('a1000000-0000-0000-0000-000000000002','media_photos',      50,'in-progress', '{"uploaded":36,"required":72,"missing_count":8}'),
('a1000000-0000-0000-0000-000000000002','content_faqs',      70,'in-progress', '{"completed":7,"total":10,"missing":["Utility billing FAQ","Noise policy","Short-term rental policy"]}'),
('a1000000-0000-0000-0000-000000000002','integrations',      40,'in-progress', '{"connected":2,"required":5,"pending":["Yardi Voyager","Apartments.com","Zillow"]}'),

-- Skyline Towers (100% — ready)
('a1000000-0000-0000-0000-000000000003','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000003','units_floor_plans',100,'complete',    '{"units_added":120,"floor_plans":8}'),
('a1000000-0000-0000-0000-000000000003','amenities',        100,'complete',    '{"amenities_count":24,"described":24}'),
('a1000000-0000-0000-0000-000000000003','media_photos',     100,'complete',    '{"uploaded":120,"required":120}'),
('a1000000-0000-0000-0000-000000000003','content_faqs',     100,'complete',    '{"completed":15,"total":15}'),
('a1000000-0000-0000-0000-000000000003','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- Northgate Apartments (42% — in-progress)
('a1000000-0000-0000-0000-000000000004','property_info',     60,'in-progress', '{"fields_filled":7,"fields_total":12,"missing":["description","virtual_tour_url","office_hours"]}'),
('a1000000-0000-0000-0000-000000000004','units_floor_plans',  0,'not-started', '{"units_added":0,"note":"No unit data entered yet"}'),
('a1000000-0000-0000-0000-000000000004','amenities',          30,'in-progress', '{"amenities_count":10,"described":3}'),
('a1000000-0000-0000-0000-000000000004','media_photos',        0,'not-started', '{"uploaded":0,"required":36,"note":"No photos uploaded"}'),
('a1000000-0000-0000-0000-000000000004','content_faqs',       50,'in-progress', '{"completed":5,"total":10}'),
('a1000000-0000-0000-0000-000000000004','integrations',       20,'in-progress', '{"connected":1,"required":5}'),

-- Maple Heights (100% — ready)
('a1000000-0000-0000-0000-000000000005','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000005','units_floor_plans',100,'complete',    '{"units_added":60,"floor_plans":7}'),
('a1000000-0000-0000-0000-000000000005','amenities',        100,'complete',    '{"amenities_count":20,"described":20}'),
('a1000000-0000-0000-0000-000000000005','media_photos',     100,'complete',    '{"uploaded":60,"required":60}'),
('a1000000-0000-0000-0000-000000000005','content_faqs',     100,'complete',    '{"completed":12,"total":12}'),
('a1000000-0000-0000-0000-000000000005','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- Oak Residences (55% — in-progress)
('a1000000-0000-0000-0000-000000000006','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000006','units_floor_plans', 70,'in-progress', '{"units_added":28,"floor_plans":2}'),
('a1000000-0000-0000-0000-000000000006','amenities',         50,'in-progress', '{"amenities_count":14,"described":7}'),
('a1000000-0000-0000-0000-000000000006','media_photos',      40,'in-progress', '{"uploaded":11,"required":28}'),
('a1000000-0000-0000-0000-000000000006','content_faqs',      40,'in-progress', '{"completed":4,"total":10}'),
('a1000000-0000-0000-0000-000000000006','integrations',      60,'in-progress', '{"connected":3,"required":5}'),

-- Cedar Grove (78% — blocked)
('a1000000-0000-0000-0000-000000000007','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000007','units_floor_plans',100,'complete',    '{"units_added":54,"floor_plans":6}'),
('a1000000-0000-0000-0000-000000000007','amenities',         90,'in-progress', '{"amenities_count":16,"described":14}'),
('a1000000-0000-0000-0000-000000000007','media_photos',      80,'in-progress', '{"uploaded":43,"required":54}'),
('a1000000-0000-0000-0000-000000000007','content_faqs',      60,'blocked',     '{"completed":6,"total":10,"missing":["Lease break policy","Short-term rental"]}'),
('a1000000-0000-0000-0000-000000000007','integrations',      60,'in-progress', '{"connected":3,"required":5}'),

-- Summit Place (30% — in-progress)
('a1000000-0000-0000-0000-000000000008','property_info',     50,'in-progress', '{"fields_filled":6,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000008','units_floor_plans', 20,'in-progress', '{"units_added":8,"note":"Only 8 of 42 units"}'),
('a1000000-0000-0000-0000-000000000008','amenities',          20,'in-progress', '{"amenities_count":8,"described":2}'),
('a1000000-0000-0000-0000-000000000008','media_photos',       10,'in-progress', '{"uploaded":4,"required":42}'),
('a1000000-0000-0000-0000-000000000008','content_faqs',       30,'in-progress', '{"completed":3,"total":10}'),
('a1000000-0000-0000-0000-000000000008','integrations',        0,'not-started', '{"connected":0,"required":5}'),

-- Harbor View (100% — ready)
('a1000000-0000-0000-0000-000000000009','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000009','units_floor_plans',100,'complete',    '{"units_added":96,"floor_plans":10}'),
('a1000000-0000-0000-0000-000000000009','amenities',        100,'complete',    '{"amenities_count":28,"described":28}'),
('a1000000-0000-0000-0000-000000000009','media_photos',     100,'complete',    '{"uploaded":96,"required":96}'),
('a1000000-0000-0000-0000-000000000009','content_faqs',     100,'complete',    '{"completed":15,"total":15}'),
('a1000000-0000-0000-0000-000000000009','integrations',     100,'complete',    '{"connected":5,"required":5}'),

-- Westfield Court (85% — in-progress)
('a1000000-0000-0000-0000-000000000010','property_info',    100,'complete',    '{"fields_filled":12,"fields_total":12}'),
('a1000000-0000-0000-0000-000000000010','units_floor_plans',100,'complete',    '{"units_added":80,"floor_plans":8}'),
('a1000000-0000-0000-0000-000000000010','amenities',        100,'complete',    '{"amenities_count":22,"described":22}'),
('a1000000-0000-0000-0000-000000000010','media_photos',      90,'in-progress', '{"uploaded":72,"required":80,"missing":["6C","14A","22B","38D"]}'),
('a1000000-0000-0000-0000-000000000010','content_faqs',      80,'in-progress', '{"completed":12,"total":15,"missing":["Short-term rental","Lease break","Subletting"]}'),
('a1000000-0000-0000-0000-000000000010','integrations',      60,'in-progress', '{"connected":3,"required":5}')

ON CONFLICT (property_id, section) DO UPDATE SET
  completion_pct = EXCLUDED.completion_pct,
  status         = EXCLUDED.status,
  metadata       = EXCLUDED.metadata,
  updated_at     = now();

-- ── PROPERTY ONBOARDING STATUS (calculated from sections) ──
-- Recalculate for all 10 properties using our helper function
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000001');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000002');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000003');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000004');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000005');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000006');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000007');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000008');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000009');
SELECT public.recalculate_onboarding_status('a1000000-0000-0000-0000-000000000010');

-- ── PROPERTY ONBOARDING BLOCKERS ────────────────────────────
INSERT INTO public.property_onboarding_blockers
  (property_id, section, type, severity, message, description, action, ai_can_fix) VALUES
-- River Lofts
('a1000000-0000-0000-0000-000000000001','content_faqs','missing_content','blocking','Missing pet policy FAQ','Pet policy FAQ required before listing goes live on Apartments.com and Zillow','Generate pet policy FAQ or enter manually',true),
('a1000000-0000-0000-0000-000000000001','integrations','sync_pending','blocking','PMS sync pending','Yardi Voyager PMS sync has not completed. Unit availability data may be stale.','Trigger manual sync or check Yardi API credentials',false),
('a1000000-0000-0000-0000-000000000001','media_photos','missing_media','warning','2 unit photos missing','Units 3B and 7A are missing professional listing photos.','Upload at least 2 photos per unit for 3B and 7A',false),
-- Parkside Commons
('a1000000-0000-0000-0000-000000000002','media_photos','missing_media','warning','Missing 8 unit photos','8 units are missing professional photos. Reduces listing quality score.','Upload professional photos for units: 1A, 1C, 2B, 3A, 4B, 5C, 6A, 7B',false),
('a1000000-0000-0000-0000-000000000002','amenities','missing_content','warning','Amenity descriptions incomplete','8 amenities are missing descriptions. Descriptions improve search ranking.','Add descriptions for: Rooftop terrace, Pet spa, Co-working space and 5 others',true),
('a1000000-0000-0000-0000-000000000002','integrations','sync_pending','warning','3 integrations not connected','Yardi Voyager, Apartments.com and Zillow are not yet connected.','Connect integrations via Settings > Integrations',false),
-- Northgate
('a1000000-0000-0000-0000-000000000004','property_info','incomplete_info','blocking','Property info incomplete','5 required property fields are missing. Cannot proceed without core info.','Complete property description, office hours, accessibility info and 2 others',true),
('a1000000-0000-0000-0000-000000000004','units_floor_plans','no_data','blocking','No unit data','No units have been added. All 36 units need to be entered.','Add units manually or sync via PMS integration',false),
('a1000000-0000-0000-0000-000000000004','media_photos','missing_media','blocking','Missing all photos','No photos uploaded for this property or any of its units.','Upload at least 10 property photos and 2 photos per unit',false),
-- Cedar Grove
('a1000000-0000-0000-0000-000000000007','content_faqs','missing_content','blocking','Lease break policy missing','Lease break policy FAQ is a legal requirement before listing.','Add lease break policy FAQ using AI generation or legal template',true),
('a1000000-0000-0000-0000-000000000007','media_photos','missing_media','warning','11 unit photos missing','11 units still need professional photos for listing.','Upload photos for units 4B, 8C, 12A and 8 others',false),
-- Oak Residences
('a1000000-0000-0000-0000-000000000006','media_photos','missing_media','warning','17 unit photos missing','17 units are missing listing photos. Quality score significantly reduced.','Schedule photo shoot for missing units',false),
('a1000000-0000-0000-0000-000000000006','content_faqs','missing_content','warning','6 FAQs incomplete','6 FAQ items are missing including Pet policy and Parking FAQ.','Generate missing FAQs using AI or enter manually',true),
-- Summit Place
('a1000000-0000-0000-0000-000000000008','property_info','incomplete_info','blocking','Property info 50% incomplete','6 required fields missing including description and office hours.','Complete all required property info fields',true),
('a1000000-0000-0000-0000-000000000008','units_floor_plans','incomplete_info','blocking','Only 8 of 42 units added','34 units are missing. Listing cannot go live until all units are entered.','Add remaining 34 units or sync via PMS',false),
('a1000000-0000-0000-0000-000000000008','integrations','no_data','blocking','No integrations connected','No integrations configured. All 5 required integrations are pending.','Connect at minimum Apartments.com and Zillow to proceed',false),
-- Westfield Court
('a1000000-0000-0000-0000-000000000010','media_photos','missing_media','warning','8 unit photos missing','8 units are missing professional photos before launch.','Upload photos for units 6C, 14A, 22B and 5 others',false),
('a1000000-0000-0000-0000-000000000010','content_faqs','missing_content','warning','3 policy FAQs missing','Short-term rental, lease break and subletting policy are missing.','Generate policy FAQs using AI content generator',true),
-- Skyline (resolved example)
('a1000000-0000-0000-0000-000000000003','content_faqs','missing_content','warning','Pet policy FAQ was missing','Pet policy FAQ was missing but has been generated.','Completed',true)
ON CONFLICT DO NOTHING;

-- Mark Skyline blocker as resolved
UPDATE public.property_onboarding_blockers
SET resolved = true, resolved_at = now() - interval '10 days'
WHERE property_id = 'a1000000-0000-0000-0000-000000000003';

-- ── PROPERTY FAQs ─────────────────────────────────────────────
INSERT INTO public.property_faqs
  (property_id, question, answer, category, ai_generated, is_published) VALUES
-- River Lofts (9 published, 3 empty placeholders)
('a1000000-0000-0000-0000-000000000001','What is the lease term?','We offer 6, 9, and 12-month lease terms. Month-to-month is available after the initial lease at a premium.','lease',false,true),
('a1000000-0000-0000-0000-000000000001','What utilities are included?','Water, trash, and recycling are included. Residents are responsible for electricity, gas, and internet.','utilities',false,true),
('a1000000-0000-0000-0000-000000000001','Is renters insurance required?','Yes, all residents must carry renters insurance with a minimum of $100,000 liability coverage.','general',false,true),
('a1000000-0000-0000-0000-000000000001','What is the move-in process?','Move-ins are scheduled Monday–Saturday 9am–5pm. A move-in inspection will be completed with your leasing agent.','move_in',false,true),
('a1000000-0000-0000-0000-000000000001','How do I submit a maintenance request?','Submit requests through the resident portal or app. Emergency maintenance is available 24/7 at (512) 555-0100.','maintenance',false,true),
('a1000000-0000-0000-0000-000000000001','What is the guest policy?','Guests may stay up to 14 consecutive days. Extended stays require management approval.','guest',false,true),
('a1000000-0000-0000-0000-000000000001','Is there a noise policy?','Quiet hours are 10pm–8am Sunday–Thursday and 11pm–9am Friday–Saturday.','noise',false,true),
('a1000000-0000-0000-0000-000000000001','What are the renewal terms?','Renewal offers are sent 90 days before lease end. Early renewal discounts are available.','lease',false,true),
('a1000000-0000-0000-0000-000000000001','What is the application process?','Apply online at riverlofts.com. We require ID, proof of income (3x rent), and a credit check.','general',false,true),
('a1000000-0000-0000-0000-000000000001','What is the pet policy?','','pet_policy',false,false),
('a1000000-0000-0000-0000-000000000001','What is the parking policy?','','parking',false,false),
('a1000000-0000-0000-0000-000000000001','What is the lease break policy?','','lease',false,false),
-- Skyline Towers (15 complete — AI generated some)
('a1000000-0000-0000-0000-000000000003','What is the pet policy?','We welcome cats and dogs up to 80 lbs. Limit 2 pets per unit. Pet deposit $500, monthly pet rent $75/pet.','pet_policy',true,true),
('a1000000-0000-0000-0000-000000000003','What is the parking policy?','One assigned garage space included. Additional spaces available at $150/month.','parking',false,true),
('a1000000-0000-0000-0000-000000000003','What is the lease term?','Standard 12-month lease. 6-month leases available at a 10% premium.','lease',false,true),
('a1000000-0000-0000-0000-000000000003','What utilities are included?','Water, trash, and recycling included. Gas and electric billed separately through Austin Energy.','utilities',false,true),
('a1000000-0000-0000-0000-000000000003','Is renters insurance required?','Yes. Minimum $100,000 liability. You may be added to our group policy for $12/month.','general',false,true),
('a1000000-0000-0000-0000-000000000003','How do I submit a maintenance request?','Use the Skyline Towers app or call our 24/7 maintenance line. Emergency response within 2 hours.','maintenance',false,true),
('a1000000-0000-0000-0000-000000000003','What is the guest policy?','Overnight guests allowed up to 10 days/month. Long-term guests must be added to the lease.','guest',false,true),
('a1000000-0000-0000-0000-000000000003','Is there a noise policy?','Quiet hours 10pm–8am daily. Pool and rooftop close at 11pm.','noise',false,true),
('a1000000-0000-0000-0000-000000000003','What is the lease break policy?','Early termination requires 60-day notice and a fee equal to 2 months rent.','lease',true,true),
('a1000000-0000-0000-0000-000000000003','What is the move-in process?','Move-ins by appointment only, 9am–6pm weekdays. Building elevator reserved in 2-hour blocks.','move_in',false,true),
('a1000000-0000-0000-0000-000000000003','Are short-term rentals allowed?','Short-term rentals (Airbnb, VRBO) are strictly prohibited per lease agreement.','general',true,true),
('a1000000-0000-0000-0000-000000000003','What is the subletting policy?','Subletting is not permitted without written management approval.','general',false,true),
('a1000000-0000-0000-0000-000000000003','What is the renewal process?','Renewal offers sent 90 days before lease end via email and resident portal.','lease',false,true),
('a1000000-0000-0000-0000-000000000003','What is the application fee?','Application fee is $75 per adult applicant, non-refundable.','general',false,true),
-- Maple Heights (12 complete)
('a1000000-0000-0000-0000-000000000005','What is the pet policy?','Cats and dogs welcome, max 2 pets, up to 60 lbs. $400 pet deposit, $60/month pet rent.','pet_policy',true,true),
('a1000000-0000-0000-0000-000000000005','What is the parking policy?','One covered spot included per unit. Additional parking $100/month.','parking',false,true),
('a1000000-0000-0000-0000-000000000005','What utilities are included?','Water, sewer, and trash included. Electricity and gas metered individually.','utilities',false,true),
('a1000000-0000-0000-0000-000000000005','How do I submit a maintenance request?','Submit via the resident portal or call (512) 555-0200.','maintenance',false,true),
('a1000000-0000-0000-0000-000000000005','What is the lease break policy?','60-day notice required. Break fee equals 1.5 months rent.','lease',true,true),
('a1000000-0000-0000-0000-000000000005','What is the lease term?','12-month standard. 6-month available with premium.','lease',false,true),
('a1000000-0000-0000-0000-000000000005','Is renters insurance required?','Yes, $100,000 minimum liability required.','general',false,true),
('a1000000-0000-0000-0000-000000000005','What is the guest policy?','Guests may stay up to 7 consecutive nights.','guest',false,true),
('a1000000-0000-0000-0000-000000000005','Is there a noise policy?','Quiet hours 10pm–8am Sunday–Thursday.','noise',false,true),
('a1000000-0000-0000-0000-000000000005','What is the move-in process?','Schedule move-in online. Elevator reserved in 2-hour slots.','move_in',false,true),
('a1000000-0000-0000-0000-000000000005','What is the application process?','Apply online. Income verification, credit check, and ID required.','general',false,true),
('a1000000-0000-0000-0000-000000000005','Are short-term rentals allowed?','Short-term rentals are not permitted.','general',false,true),
-- Northgate (5 published, 5 missing)
('a1000000-0000-0000-0000-000000000004','What is the lease term?','12-month leases only at this time.','lease',false,true),
('a1000000-0000-0000-0000-000000000004','What utilities are included?','Water and trash included. All other utilities resident responsibility.','utilities',false,true),
('a1000000-0000-0000-0000-000000000004','How do I submit a maintenance request?','Call (512) 555-0300 during business hours.','maintenance',false,true),
('a1000000-0000-0000-0000-000000000004','What is the application process?','Contact leasing office at northgate@example.com.','general',false,true),
('a1000000-0000-0000-0000-000000000004','Is renters insurance required?','Strongly recommended but not required.','general',false,true),
('a1000000-0000-0000-0000-000000000004','What is the pet policy?','','pet_policy',false,false),
('a1000000-0000-0000-0000-000000000004','What is the parking policy?','','parking',false,false),
('a1000000-0000-0000-0000-000000000004','What are the utility billing details?','','utilities',false,false),
('a1000000-0000-0000-0000-000000000004','What is the guest policy?','','guest',false,false),
('a1000000-0000-0000-0000-000000000004','What are the renewal terms?','','lease',false,false)
ON CONFLICT DO NOTHING;

-- ── PROPERTY AMENITIES ───────────────────────────────────────
INSERT INTO public.property_amenities
  (property_id, name, description, category, ai_generated) VALUES
-- River Lofts (all 18 described)
('a1000000-0000-0000-0000-000000000001','Pool','Resort-style saltwater pool with sun deck, lounge chairs, and poolside cabanas.','outdoor',false),
('a1000000-0000-0000-0000-000000000001','Gym','State-of-the-art fitness center with Peloton bikes, free weights, and TRX equipment. Open 24/7.','wellness',false),
('a1000000-0000-0000-0000-000000000001','Rooftop Deck','Panoramic rooftop terrace with seating, fire pits, and stunning city views. Open until 11pm.','outdoor',false),
('a1000000-0000-0000-0000-000000000001','Pet Spa','Full-service pet grooming station with wash stations, dryers, and grooming tools.','pet',false),
('a1000000-0000-0000-0000-000000000001','Co-working Space','Modern co-working lounge with private pods, high-speed Wi-Fi, and printing services.','indoor',false),
('a1000000-0000-0000-0000-000000000001','EV Charging','10 Tesla and universal EV charging stations in the parking garage.','parking',false),
('a1000000-0000-0000-0000-000000000001','Package Lockers','Smart package lockers with 24/7 access. Text notifications when packages arrive.','tech',false),
('a1000000-0000-0000-0000-000000000001','Bike Storage','Secure indoor bike storage room with repair station and pump.','indoor',false),
('a1000000-0000-0000-0000-000000000001','Guest Suite','Fully furnished guest suite available for resident guests at $75/night.','indoor',false),
('a1000000-0000-0000-0000-000000000001','Movie Lounge','Private screening room with 4K projector and surround sound. Seats 20.','indoor',false),
('a1000000-0000-0000-0000-000000000001','BBQ Area','Outdoor grilling area with gas BBQ stations, dining tables, and string lights.','outdoor',false),
('a1000000-0000-0000-0000-000000000001','Dog Park','Fully fenced dog park with agility equipment and water stations.','pet',false),
('a1000000-0000-0000-0000-000000000001','Concierge','On-site concierge available Monday–Friday 9am–6pm.','indoor',false),
('a1000000-0000-0000-0000-000000000001','Valet Parking','Optional valet parking service available evenings and weekends. $200/month.','parking',false),
('a1000000-0000-0000-0000-000000000001','Storage Units','Private storage units from 5x5 to 10x10 ft. Available from $45/month.','indoor',false),
('a1000000-0000-0000-0000-000000000001','Yoga Studio','Dedicated yoga and meditation studio with natural light and premium flooring.','wellness',false),
('a1000000-0000-0000-0000-000000000001','Coffee Bar','Complimentary coffee and tea bar in the lobby. Featuring locally roasted Austin blends.','indoor',false),
('a1000000-0000-0000-0000-000000000001','Sky Lounge','Exclusive resident sky lounge on the top floor with bar area and city views.','indoor',false),
-- Parkside Commons (12 described, 8 empty — blockers)
('a1000000-0000-0000-0000-000000000002','Pool','Community pool with sun deck and lounge seating.','outdoor',false),
('a1000000-0000-0000-0000-000000000002','Gym','Fitness center with cardio and strength training equipment.','wellness',false),
('a1000000-0000-0000-0000-000000000002','BBQ Area','Outdoor BBQ stations with gas grills and picnic tables.','outdoor',false),
('a1000000-0000-0000-0000-000000000002','Dog Park','Fenced dog park with water station.','pet',false),
('a1000000-0000-0000-0000-000000000002','Package Lockers','24/7 smart package locker system.','tech',false),
('a1000000-0000-0000-0000-000000000002','Bike Storage','Secured indoor bike room.','indoor',false),
('a1000000-0000-0000-0000-000000000002','Playground','Children''s playground with safety surfaces.','outdoor',false),
('a1000000-0000-0000-0000-000000000002','Car Wash','Self-service car wash station.','parking',false),
('a1000000-0000-0000-0000-000000000002','Fitness Studio','Dedicated group fitness studio.','wellness',false),
('a1000000-0000-0000-0000-000000000002','EV Charging','EV charging stations in parking area.','parking',false),
('a1000000-0000-0000-0000-000000000002','Guest Suite','Furnished guest suite for resident visitors.','indoor',false),
('a1000000-0000-0000-0000-000000000002','Movie Lounge','Private screening room for residents.','indoor',false),
('a1000000-0000-0000-0000-000000000002','Rooftop Terrace','','outdoor',false),
('a1000000-0000-0000-0000-000000000002','Pet Spa','','pet',false),
('a1000000-0000-0000-0000-000000000002','Co-working Space','','indoor',false),
('a1000000-0000-0000-0000-000000000002','Yoga Studio','','wellness',false),
('a1000000-0000-0000-0000-000000000002','Coffee Bar','','indoor',false),
('a1000000-0000-0000-0000-000000000002','Sky Lounge','','indoor',false),
('a1000000-0000-0000-0000-000000000002','Wine Cellar','','indoor',false),
('a1000000-0000-0000-0000-000000000002','Business Center','','indoor',false)
ON CONFLICT DO NOTHING;

-- ── PROPERTY INTEGRATION STATUS ──────────────────────────────
INSERT INTO public.property_integration_status
  (property_id, integration_name, category, status, last_sync_at, daily_api_calls, daily_api_limit) VALUES
-- River Lofts (4 connected, 1 pending)
('a1000000-0000-0000-0000-000000000001','apartments_com','lead_sources','connected',now()-interval '2 hours',245,1000),
('a1000000-0000-0000-0000-000000000001','zillow','lead_sources','connected',now()-interval '4 hours',182,1000),
('a1000000-0000-0000-0000-000000000001','rent_com','lead_sources','connected',now()-interval '1 day',98,1000),
('a1000000-0000-0000-0000-000000000001','appfolio','property_management','connected',now()-interval '1 hour',320,1000),
('a1000000-0000-0000-0000-000000000001','yardi','property_management','not_connected',NULL,0,1000),
-- Parkside Commons (2 connected)
('a1000000-0000-0000-0000-000000000002','apartments_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000002','zillow','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000002','rent_com','lead_sources','connected',now()-interval '2 days',67,1000),
('a1000000-0000-0000-0000-000000000002','appfolio','property_management','connected',now()-interval '1 day',145,1000),
('a1000000-0000-0000-0000-000000000002','yardi','property_management','not_connected',NULL,0,1000),
-- Skyline Towers (all 5 connected)
('a1000000-0000-0000-0000-000000000003','apartments_com','lead_sources','connected',now()-interval '30 minutes',847,1000),
('a1000000-0000-0000-0000-000000000003','zillow','lead_sources','connected',now()-interval '1 hour',512,1000),
('a1000000-0000-0000-0000-000000000003','rent_com','lead_sources','connected',now()-interval '2 hours',398,1000),
('a1000000-0000-0000-0000-000000000003','appfolio','property_management','connected',now()-interval '30 minutes',621,1000),
('a1000000-0000-0000-0000-000000000003','yardi','property_management','connected',now()-interval '1 hour',435,1000),
-- Northgate (1 connected)
('a1000000-0000-0000-0000-000000000004','apartments_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000004','zillow','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000004','rent_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000004','appfolio','property_management','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000004','yardi','property_management','connected',now()-interval '5 days',12,1000),
-- Maple Heights (all 5 connected)
('a1000000-0000-0000-0000-000000000005','apartments_com','lead_sources','connected',now()-interval '1 hour',312,1000),
('a1000000-0000-0000-0000-000000000005','zillow','lead_sources','connected',now()-interval '2 hours',278,1000),
('a1000000-0000-0000-0000-000000000005','rent_com','lead_sources','connected',now()-interval '1 day',189,1000),
('a1000000-0000-0000-0000-000000000005','appfolio','property_management','connected',now()-interval '1 hour',445,1000),
('a1000000-0000-0000-0000-000000000005','yardi','property_management','connected',now()-interval '2 hours',367,1000),
-- Oak Residences (3 connected)
('a1000000-0000-0000-0000-000000000006','apartments_com','lead_sources','connected',now()-interval '1 day',134,1000),
('a1000000-0000-0000-0000-000000000006','zillow','lead_sources','connected',now()-interval '1 day',98,1000),
('a1000000-0000-0000-0000-000000000006','rent_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000006','appfolio','property_management','connected',now()-interval '3 hours',256,1000),
('a1000000-0000-0000-0000-000000000006','yardi','property_management','not_connected',NULL,0,1000),
-- Cedar Grove (3 connected)
('a1000000-0000-0000-0000-000000000007','apartments_com','lead_sources','connected',now()-interval '2 hours',289,1000),
('a1000000-0000-0000-0000-000000000007','zillow','lead_sources','connected',now()-interval '3 hours',201,1000),
('a1000000-0000-0000-0000-000000000007','rent_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000007','appfolio','property_management','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000007','yardi','property_management','connected',now()-interval '1 day',178,1000),
-- Summit Place (0 connected)
('a1000000-0000-0000-0000-000000000008','apartments_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000008','zillow','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000008','rent_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000008','appfolio','property_management','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000008','yardi','property_management','not_connected',NULL,0,1000),
-- Harbor View (all 5 connected)
('a1000000-0000-0000-0000-000000000009','apartments_com','lead_sources','connected',now()-interval '30 minutes',567,1000),
('a1000000-0000-0000-0000-000000000009','zillow','lead_sources','connected',now()-interval '1 hour',423,1000),
('a1000000-0000-0000-0000-000000000009','rent_com','lead_sources','connected',now()-interval '2 hours',312,1000),
('a1000000-0000-0000-0000-000000000009','appfolio','property_management','connected',now()-interval '30 minutes',689,1000),
('a1000000-0000-0000-0000-000000000009','yardi','property_management','connected',now()-interval '1 hour',534,1000),
-- Westfield Court (3 connected)
('a1000000-0000-0000-0000-000000000010','apartments_com','lead_sources','connected',now()-interval '2 hours',378,1000),
('a1000000-0000-0000-0000-000000000010','zillow','lead_sources','connected',now()-interval '3 hours',289,1000),
('a1000000-0000-0000-0000-000000000010','rent_com','lead_sources','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000010','appfolio','property_management','not_connected',NULL,0,1000),
('a1000000-0000-0000-0000-000000000010','yardi','property_management','connected',now()-interval '1 hour',445,1000)

ON CONFLICT (property_id, integration_name) DO UPDATE SET
  status         = EXCLUDED.status,
  last_sync_at   = EXCLUDED.last_sync_at,
  daily_api_calls= EXCLUDED.daily_api_calls,
  updated_at     = now();

-- ── PROPERTY AI CONTENT JOBS ─────────────────────────────────
INSERT INTO public.property_ai_content_jobs
  (property_id, section, content_type, status, prompt_used,
   generated_content, triggered_by, created_at, completed_at) VALUES
('a1000000-0000-0000-0000-000000000003','content_faqs','faq','completed',
 'Generate pet policy FAQ for Skyline Towers Austin TX luxury 120-unit high-rise',
 '{"question":"What is the pet policy?","answer":"We welcome cats and dogs up to 80 lbs..."}',
 'admin@aigentless.com', now()-interval '15 days', now()-interval '15 days'+interval '8 seconds'),
('a1000000-0000-0000-0000-000000000005','amenities','amenity_description','completed',
 'Generate descriptions for 12 amenities at Maple Heights apartments Austin TX',
 '{"amenities_updated":12}',
 'admin@aigentless.com', now()-interval '8 days', now()-interval '8 days'+interval '12 seconds'),
('a1000000-0000-0000-0000-000000000001','content_faqs','faq','pending',
 NULL, NULL,
 'admin@aigentless.com', now()-interval '2 minutes', NULL),
('a1000000-0000-0000-0000-000000000004','property_info','property_description','failed',
 'Generate property description for Northgate Apartments Austin TX',
 NULL,
 'admin@aigentless.com', now()-interval '2 days', now()-interval '2 days'+interval '30 seconds')
ON CONFLICT DO NOTHING;

-- Update failed job error message
UPDATE public.property_ai_content_jobs
SET error_message = 'LLM API timeout after 30 seconds. Please try again.'
WHERE property_id = 'a1000000-0000-0000-0000-000000000004'
  AND status = 'failed';

DO $$
BEGIN
  RAISE NOTICE '✅ Seed complete! All Category 1 + 2 tables populated.';
  RAISE NOTICE '   Properties: 10 | Floorplans: 20 | Units: 30';
  RAISE NOTICE '   Sections: 60 | Blockers: 19 | FAQs: 47';
  RAISE NOTICE '   Amenities: 38 | Integrations: 50 | AI Jobs: 4';
END $$;
