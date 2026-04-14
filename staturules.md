# Status Rules by Page

This document lists all runtime status/badge values currently used across dashboard pages, with their generation logic and data source.

## 1) Lead Prioritization (`/users`)

### Badge: Lead Heat (`hot`, `warm`, `cold`)
- **Data source:** `prospect_events` + `bookings` (scoped to selected `days` window)
- **Backend rule location:** `services/dashboard_service.py` (`_heat_from_engagement`)
- **Logic:**
  - `cold` if no events in window and no booking in window.
  - `hot` if any of:
    - has booking in window, or
    - events in window >= 3, or
    - last activity < 24h
  - `warm` if any of:
    - events in window >= 1, or
    - last activity < 7 days
  - else `cold`

### Badge: Lead Priority (`critical`, `moderate`, `low`)
- **Data source:** `prospects.applied`, `prospects.leased`
- **Backend rule location:** `services/dashboard_service.py` (`_priority_from_flags`)
- **Logic:**
  - `critical` => `applied = false` and `leased = false`
  - `moderate` => `applied = true` and `leased = false`
  - `low` => otherwise (leased true)

### UI-only display mapping
- **Frontend location:** `Aileasingintelligencedashboard/src/pages/UsersPage.tsx`
- Heat badge colors map directly from backend heat.
- Priority badge icon/text maps directly from backend priority.

---

## 2) Inventory Intelligence (`/packages`)

### Badge: Unit Status (`atRisk`, `stale`, `healthy`)
- **Data source:** inventory signals computed from:
  - tours count in window
  - applications count in window
  - conversion %
  - vacancy days
  - selected window (`7/30/90`)
- **Backend rule location:** `services/dashboard_service.py` (`_inventory_status_from_signals`)
- **Logic (ordered):**
  - `atRisk` if `tours >= 3` and `apps == 0`
  - `atRisk` if long window (90d) and `vacancy_days >= 30` and `conv_pct < 75`
  - `atRisk` if `vacancy_days >= max(5, int(window_days * 0.55))` and conversion below window cutoff:
    - 7d cutoff: `< 55`
    - 30d cutoff: `< 60`
    - 90d cutoff: `< 68`
  - `atRisk` if `conv_pct < 45`
  - `stale` if `45 <= conv_pct < 75`
  - `healthy` if `conv_pct >= 75`

### UI-only display mapping
- **Frontend location:** `Aileasingintelligencedashboard/src/pages/PackagesPage.tsx`
- `atRisk` -> badge text `critical`
- `stale` -> badge text `attention`
- `healthy` -> badge text `healthy`

---

## 3) Property Onboarding (`/properties`)

### Badge: Property Status (`ready`, `in-progress`, `blocked`)
- **Data source:** onboarding payload from backend.
- **Backend normalization location:** `services/live_ui_payloads.py` (`_normalize_onboarding_status_ui`)
- **Logic:**
  - Raw `ready` -> `ready`
  - Raw `blocked` -> `blocked`
  - everything else -> `inProgress` (payload format)

### Heuristic fallback when onboarding table data is missing
- **Backend location:** `services/live_ui_payloads.py` (`_heuristic_onboarding_row`)
- **Inputs:** `properties.go_live_date` + deterministic seed from property id
- **Logic:**
  - go-live <= -7 days -> `ready` with ~90-99 completeness
  - go-live <= +14 days -> `in-progress` with ~62-86 completeness
  - go-live farther future -> `blocked` with ~35-54 completeness
  - no parseable date -> `in-progress` with ~40-69 completeness

### UI-only display mapping
- **Frontend location:** `Aileasingintelligencedashboard/src/pages/PropertiesPage.tsx`
- `ready`, `in-progress`, `blocked` mapped to colored pills.

---

## 4) Portfolio Overview (`/analytics`)

### Badge: Property Rating (`Excellent`, `Good`, `Needs Attention`)
- **Data source:** `properties`, `units`, and inventory `vacantUnits` metrics
- **Backend rule location:** `services/live_ui_payloads.py`
  - score calc in `build_portfolio_overview_from_inv`
  - rating thresholds in `_portfolio_rating_from_signals`
- **Health score formula:**
  - `health = round(58 + 0.5*conversion - 2.0*vacancy_rate + min(12, tours*0.6))`
  - clamped to `45..98`
- **Rating thresholds:**
  - `health >= 92` => `Excellent`
  - `health >= 82` => `Good`
  - else => `Needs Attention`

### Internal status used by UI cards
- **Backend location:** same function above
- **Logic:**
  - `status = healthy` for ratings `Excellent` and `Good`
  - `status = attention` for rating `Needs Attention`

### Portfolio recommendations priority tags (same page, lower section)
- **Source:** LLM (`_llm_portfolio_recommendations`) or fallback
- **Backend location:** `services/live_ui_payloads.py`
- **Tag mapping from LLM `priority`:**
  - `high` -> `High priority` (red)
  - `opportunity` -> `Opportunity` (green)
  - default -> `Medium priority` (yellow)

---

## 5) Home Dashboard (`/`)

### Badge: At-Risk Units card (`high`, `medium`)
- **Data source:** inventory `vacantUnits` (`status`, `days`, `whyMatters`)
- **Backend location:** `services/live_ui_payloads.py` (`build_home_payload_from_parts`)
- **Inclusion logic:**
  - include unit if `status == atRisk` OR `days >= 10`
- **Risk badge logic:**
  - `high` if `status == atRisk`
  - else `medium`

### Badge: Follow-Up Queue heat (`hot`, `warm`)
- **Data source:** leads summary rows (`status`)
- **Backend location:** same function above
- **Logic:**
  - `hot` if lead status is exactly `hot`
  - else `warm` (cold leads are currently coerced to warm for this widget)

### Badge: Launch Blockers tag (`blocking`)
- **Data source:** onboarding payload (`status`, `blockers`)
- **Backend location:** same function above
- **Logic:**
  - include property when onboarding status is `blocked` OR blockers list is non-empty
  - emitted tag is `blocking`

### Badge: Tour Insights tone (`positive`, `negative`)
- **Data source:** `prospect_events` tour mentions grouped by property
- **Backend location:** same function above
- **Logic:**
  - `negative` if mentions < threshold
  - `positive` otherwise
  - threshold from template `tourMentionsLowThreshold` (default `3`)

### Priority Actions chip (`Critical` / `High`) mapping
- **Data source:** template JSON (`home_ui_copy`) `priorityActions.items[].tag`
- **Backend:** passes tag through
- **Frontend location:** `Aileasingintelligencedashboard/src/pages/HomePage.tsx`
- **Mapping:**
  - tag `high` -> chip label `High`
  - any other value -> chip label `Critical`

---

## 6) Weekly Brief (`/ai`)

### Status-like fields
- No strict operational status badge set (like hot/warm/atRisk) is computed for this page.
- The page uses semantic sections (`wins`, `blockers`, `objections`) from:
  - fallback rule-based digest (`build_weekly_brief`)
  - or LLM enrichment (`enrich_lesa_ai_page`)

---

## Notes

- For canonical operational statuses, backend is source-of-truth:
  - Lead heat/priority: `services/dashboard_service.py`
  - Inventory unit risk status: `services/dashboard_service.py`
  - Onboarding and portfolio runtime status/rating: `services/live_ui_payloads.py`
- Some pages apply UI label remapping (`atRisk` -> `critical`, etc.) in frontend for presentation only.
