# Status rules by page

Each section follows: **Page** → **Card** → **status badge** → **rules** (data source and logic). Paths refer to this repo (`aigentless-operational-intelligence-system`) and the dashboard app (`Aileasingintelligencedashboard`).

---

## Home (`/`)

### Daily AI Brief
- **Status badge:** *(none — narrative only)*
- **Rules:** Copy comes from home UI template (`dailyAiBrief` in Supabase-loaded JSON via `load_home_ui_copy`). Fallback paragraphs are merged into **one** paragraph, `lead` stripped, and placeholders filled with `format_template` (`vac_n`, `hot_n`, `followup_n`, `at_risk_n`, `d`). Optional LLM rewrite: `services/home_llm.py` (`enrich_home_narrative_llm`) using metrics from `services/live_ui_payloads.py` (`build_home_payload_from_parts`). Frontend renders a single `<p>` from joined `paragraphs[].body` — `Aileasingintelligencedashboard/src/pages/HomePage.tsx`.

### Priority Actions
- **Status badge:** `Critical` | `High` (pill)
- **Rules:** Items from template `priorityActions.items`; each `tag` is passed through (`high` → **High**, anything else → **Critical** on the client). `ctaPath` defaults from title keywords (inventory → `/packages`, follow-up/pipeline/leads → `/users`, onboarding/blocker/launch → `/properties`, else `/analytics`). Rows are **full-row links** to `ctaPath`. **UI:** list preview capped at **5** rows (`HOME_LIST_PREVIEW_MAX`); header counts use API totals, not preview length.

### At-risk units (portfolio strip)
- **Status badge:** `high` | `medium` (risk pill — labels from `ui.labels`, e.g. High / Medium)
- **Rules:** Built in `build_home_payload_from_parts`. Includes a vacant unit if `status == "atRisk"` **or** `days >= 10`. **`high`** if inventory `status == "atRisk"`; else **`medium`**. `reason` from unit `whyMatters` or template fallback. Summary value = count of included units (up to 20 built server-side; UI shows first 5). CTA default `/packages`.

### Launch blockers
- **Status badge:** `blocking` (and client supports `warning`, but live payload uses `blocking`)
- **Rules:** From onboarding payload: property included if onboarding `status == "blocked"` **or** `blockers` non-empty. `tag` emitted as **`blocking`**. `percent` from onboarding completeness. Summary = count of such properties. CTA default `/properties`.

### Follow-up queue
- **Status badge:** `hot` | `warm` (heat pill; `cold` is not shown — see rules)
- **Rules:** Rows from leads summary `data` (prospects with a tour). Backend sets `heat` from lead `status` (`hot` vs else → **`warm`**; **`cold` becomes `warm`** in `build_home_payload_from_parts`). Channel alternates by row index (`sms` / `email`). Summary = row count. CTA default `/users`.

### Tour Insights
- **Status badge:** Row tone `positive` | `negative` (icon circle: thumbs up / thumbs down; not a text pill)
- **Header trend:** `trendValue` e.g. `+12%` or `-5%` — **green / red** and up/down icon from sign; compares tour-related event count in the current window to the **prior window of equal length**.
- **Rules:** `prospect_events` with `"tour"` in `event`, grouped by `property_id`. `tourMentionsLowThreshold` (default **3**): `mentions < threshold` → **`negative`** tone and “below typical” copy; else **`positive`**. Subtitle from template with `{d}` and `{tour_total}`. Recommended action title/body from template, optionally replaced by `enrich_home_narrative_llm`. CTA default `/ai`.

---

## Lead Prioritization (`/users`)

### Lead list row — Heat
- **Status badge:** `hot` | `warm` | `cold`
- **Rules:** `services/dashboard_service.py` — `_heat_from_engagement(events_in_window, last_ts, created, has_booking_in_window)`. **`cold`** if no events in window and no booking in window. **`hot`** if booking in window, or events in window ≥ 3, or last activity within 24 hours. **`warm`** if events ≥ 1 or last activity within 7 days. Otherwise **`cold`**. UI: `Aileasingintelligencedashboard/src/pages/UsersPage.tsx` (`HeatPill`, filters).

### Lead list row — Priority
- **Status badge:** `critical` | `moderate` | `low` (pill)
- **Rules:** For each row appended in `_build_leads_summary_sync`, `priority = "critical" if has_toured else "moderate"` with `has_toured = True` for all rows that pass the filter (prospects without a resolved tour timestamp are **skipped**). So **currently all listed leads emit `critical`** for priority. `_priority_from_flags` exists in the same file but is **not** called by this pipeline. Unknown API values normalize to **`low`** in the client.

### Lead detail / AI fields
- **Status badge:** *(none beyond heat + priority)*
- **Rules:** When `OPENAI_API_KEY` is set, `enrich_leads_summary_rows` (`services/lead_card_llm.py`) fills recommended actions, drafts, etc.; timing phrasing (e.g. follow-up cadence) is model-guided, not a fixed “email in N days” rule in code.

---

## Inventory Intelligence (`/packages`)

### Vacant unit row — Status
- **Status badge (API):** `atRisk` | `stale` | `healthy` → **UI labels:** `critical` | `attention` | `healthy`
- **Rules:** `services/dashboard_service.py` — `_inventory_status_from_signals(conv_pct, vacancy_days, window_days, tours, apps)` (ordered checks):  
  - **`atRisk`** if `tours >= 3` and `apps == 0`  
  - **`atRisk`** if `window_days >= 90` and `vacancy_days >= 30` and `conv_pct < 75`  
  - **`atRisk`** if `vacancy_days >= max(5, int(window_days * 0.55))` and conversion below cutoff: **55** (7d), **60** (30d), **68** (90d)  
  - **`atRisk`** if `conv_pct < 45`  
  - **`stale`** if `45 <= conv_pct < 75`  
  - **`healthy`** if `conv_pct >= 75`  
  UI: `PackagesPage.tsx` (`StatusBadge`, `DetailStatusBadge`).

### KPI / filter chips (counts)
- **Status badge:** Counts by `atRisk` / `stale` / `healthy` (same semantics as unit status)
- **Rules:** Client aggregates `vacantUnits` for summary cards and status filter tabs.

### Unit detail / “View full details”
- **Status badge:** Same unit status as row
- **Rules:** Extra fields and recent feedbacks from `GET /inventory/vacant-units/{unit_id}/detail` (`routes/dashboard_routes.py`, `dashboard_service._inventory_unit_detail_sync`). Guidance copy aligns with `_inventory_unit_guidance` in `dashboard_service.py`.

---

## Property Onboarding (`/properties`)

### Property list row — Launch status
- **Status badge:** `blocked` | `in-progress` | `ready`
- **Rules:** Payload from `build_onboarding_payload` / normalization `services/live_ui_payloads.py` (`_normalize_onboarding_status_ui`): raw **`ready`** → ready; **`blocked`** → blocked; else → **in progress** (internal `inProgress`; UI hyphen **`in-progress`**). If DB onboarding is thin, `_heuristic_onboarding_row` can synthesize status from `go_live_date` and deterministic spread. UI: `PropertiesPage.tsx` (`StatusBadge`).

### Summary metric cards (Ready / In Progress / Blocked / Avg completeness / Lead events)
- **Status badge:** *(numeric / label cards, not risk pills)*
- **Rules:** Counts and averages from onboarding rows in `build_onboarding_payload` output.

---

## Portfolio Overview (`/analytics`)

### Metric cards (Occupancy, Tour to App avg, Avg vacancy days)
- **Status badge:** *(none)*
- **Rules:** `build_portfolio_overview_from_inv` in `live_ui_payloads.py` — occupancy from units + vacant inventory; avg conversion and vacancy days from vacant-unit sample.

### Property cards — Health / rating
- **Status badge (UI):** `PropertyStatusBadge` maps API `status` → pill text: **`healthy`** → “Excellent”, **`watch`** → “Good”, **`attention`** → “Needs Attention” (`AnalyticsPage.tsx`).
- **Rules:** Per-property **`raw_health`** = `74 + 0.65*conv_delta - 2.2*max(0,vac_delta) - 0.9*vacancy_rate + min(8, tours*0.35)` (vs portfolio averages), clamped to **45–98** as `base_health`. Properties sorted by `raw_health`; **top ~35%** → payload **`rating` “Excellent”**, **`status` `healthy`**, health forced ≥ 88; **bottom ~25%** → **`rating` “Needs Attention”**, **`status` `attention`**, health capped ≤ 79; **middle** → **`rating` “Good”**, **`status` `healthy`**, health ~80–89. The API also exposes string **`rating`** for Excellent vs Good; the current grid badge reads only **`status`**, and both top and middle tiers use **`healthy`**, so “Good” vs “Excellent” may not differ in the pill until the client uses **`rating`**. **`_portfolio_rating_from_signals`** exists but is **not** used in this builder.

### AI Recommendations list
- **Status badge:** Tag pills e.g. **High priority** (red), **Opportunity** (green), **Medium priority** (yellow)
- **Rules:** Prefer OpenAI JSON (`_llm_portfolio_recommendations`): maps LLM `priority` **`high`** → High priority, **`opportunity`** → Opportunity, else Medium priority. If LLM skipped (no key, `SKIP_PORTFOLIO_RECS_LLM`, or error), `_fallback_portfolio_recommendations` uses non-healthy properties and tags **High priority**.

---

## Lesa AI — Weekly Operator Brief (`/ai`)

### Executive Summary, Wins, Blockers, Objections, Next Actions
- **Status badge:** *(none — section copy and bullets)*
- **Rules:** Payload from weekly brief builder (`build_weekly_brief` in `live_ui_payloads.py`) and optional LLM enrichment (`enrich_lesa_ai_page` if configured). No `hot` / `atRisk`-style enum for this page.

---

## Settings (`/settings`) and Profile (`/profile`)

### Page-level
- **Status badge:** *(none documented)*
- **Rules:** Static UI; no shared operational status pipeline with the dashboard services above.

---

## Source-of-truth quick map

| Area | Primary backend |
|------|-----------------|
| Lead heat | `dashboard_service.py` — `_heat_from_engagement` |
| Lead row priority (current API) | `dashboard_service.py` — `_build_leads_summary_sync` (not `_priority_from_flags`) |
| Inventory unit status | `dashboard_service.py` — `_inventory_status_from_signals` |
| Home widgets + tour trend | `live_ui_payloads.py` — `build_home_payload_from_parts`; narrative LLM — `home_llm.py` |
| Onboarding list | `live_ui_payloads.py` — onboarding builders + `_normalize_onboarding_status_ui` |
| Portfolio overview + property rating bands | `live_ui_payloads.py` — `build_portfolio_overview_from_inv` |

Some API values are **relabeled in the browser only** (e.g. inventory `atRisk` → pill text **`critical`**).
