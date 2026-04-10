# Dashboard Status Logic (Inventory + Leads)

This document explains how status badges and key metrics are produced for:

- Inventory Intelligence tab
- Lead Prioritization tab

It answers:

- where the logic is written
- what comes from database tables vs computed at API/UI time
- status rules and meanings

## Source of Truth

Primary backend logic lives in:

- `services/dashboard_service.py` (leads + inventory metrics)
- `services/live_ui_payloads.py` (home, onboarding, portfolio, brief, integrations, profile, header, navigation — **no `ui_payloads` table**)

Frontend rendering for these two pages lives in:

- `Aileasingintelligencedashboard/src/pages/PackagesPage.tsx` (Inventory)
- `Aileasingintelligencedashboard/src/pages/UsersPage.tsx` (Leads)

## 1) Inventory Intelligence

### Where status is computed

Backend function:

- `_build_inventory_vacant_sync(property_id, days)` in `services/dashboard_service.py`

Helper rules:

- `_conversion_rate_pct(tours, apps)`
- `_inventory_status_from_conversion(conv_pct)`
- `_days_vacant(available_date, fallback)`

### Is inventory status saved in DB?

No. Inventory status is computed at API response creation time.  
The API returns status per row, but there is no persistent `inventory_status` column used as source of truth.

### Tables used

- `spaces` (vacancy records, `available_date`, `availability_status`, `unit_id`)
- `units` (`unit`, `property_id`, `floorplan_id`, dates)
- `properties` (property display name)
- `tour_steps` (tour counts by `unit_id`)
- `bookings` (application proxy counts by `floorplan_id` and time window)
- `floorplans` (bedrooms, mapping)

### Field meanings in inventory rows

- `days`: days vacant (from `spaces.available_date`, fallback to timestamps)
- `tours`: number of tour steps linked to that unit
- `apps`: booking/application count (derived from floorplan bookings, normalized for row consistency)
- `conv`: conversion percent from tours/apps
- `status`: derived from `conv` using thresholds below

### Status rules and meaning (Inventory)

- `atRisk` (shown as **critical** in UI): conversion `< 60%`  
  Meaning: high risk, poor unit conversion health
- `stale` (shown as **attention/moderate** in UI): conversion `60% to 90%`
- `healthy`: conversion `> 90%`

## 2) Lead Prioritization

### Two badges shown per lead row

1. Heat badge: `hot | warm | cold`
2. Priority badge: `critical | moderate | low`

### Where lead badges are computed

Backend function:

- `_build_leads_summary_sync(property_id, days)` in `services/dashboard_service.py`

Helpers:

- `_heat_from_engagement(events, last_ts, created_ts, has_booking)`
- `_priority_from_flags(applied, leased)`

### Are lead statuses saved in DB?

For this tab, badge values are computed dynamically in API assembly.

- Heat (`hot/warm/cold`) is computed from event/booking recency and counts.
- Priority (`critical/moderate/low`) is computed from prospect state flags.

They are not directly read from a persisted status column for this dashboard API.

### Tables used

- `prospects` (`id`, names, `applied`, `leased`, `created_at`, `ignore`)
- `prospect_events` (`prospect_id`, `property_id`, `event`, `timestamp`)
- `bookings` (`profile_id`, `start_time`, optional tour fallback)
- `properties` (name lookup)
- `units` (display unit mapping by property)

### Status rules and meaning (Leads)

#### Heat badge (`hot/warm/cold`)

Computed from selected date window (`days` filter: 7/30/90), recency, and bookings.

- `hot` if:
  - prospect has booking in selected window, or
  - `>= 3` events in selected window, or
  - last activity `< 24h`
- `warm` if:
  - `>= 1` event in selected window, or
  - last activity `< 7 days`
- `cold`:
  - everything else (low/old activity)

Meaning:

- `hot`: immediate engagement potential
- `warm`: active but less urgent than hot
- `cold`: low recent engagement

#### Priority badge (`critical/moderate/low`)

Computed from `prospects.applied` + `prospects.leased`:

- `critical`: not applied and not leased
- `moderate`: applied and not leased
- `low`: all other cases (typically already leased)

Meaning:

- `critical`: highest follow-up urgency
- `moderate`: medium urgency
- `low`: lowest urgency

## KPI Cards on Lead Prioritization page

In `UsersPage.tsx` (not persisted in DB):

- **Avg. conversion likelihood** — average of unit `conv` values from the live inventory payload (`/api/inventory/vacant-units`).
- **Potential revenue at risk** — derived from lead heat counts with a simple weighting formula in the UI.

The trend line (`+12% this week`) is static display text unless you wire real week-over-week analytics.

## Legacy `ui_payloads` table

The API **does not read** `public.ui_payloads` anymore. After you verify staging/production, you may run `sql/drop_ui_payloads.sql` to drop the table. Branding copy for the header can be overridden with env vars (see `build_header_payload` in `services/live_ui_payloads.py`).

