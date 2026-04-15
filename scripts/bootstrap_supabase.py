import json
import os
import random
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import psycopg
from dotenv import load_dotenv

load_dotenv()


def _require_db_url() -> str:
    db_url = (
        os.getenv("SUPABASE_DB_URL", "").strip()
        or os.getenv("DATABASE_URL", "").strip()
        or os.getenv("POSTGRES_URL", "").strip()
    )
    if not db_url:
        raise RuntimeError("Set SUPABASE_DB_URL (or DATABASE_URL/POSTGRES_URL) in .env")
    return db_url


DDL_STATEMENTS = [
    """
    create table if not exists public.booking_payments (
      id uuid default gen_random_uuid(),
      booking_id text,
      property_id text,
      payment_intent_id text,
      collateral_amount text not null,
      payment_status text not null default 'pending',
      captured_amount integer default 0,
      created_at timestamptz default now(),
      updated_at timestamptz default now(),
      profile_id uuid,
      primary key (id)
    );
    """,
    """
    create table if not exists public.bookings (
      id uuid default gen_random_uuid(),
      created_at timestamptz not null default now(),
      floorplan_id text,
      start_time timestamptz not null,
      end_time timestamptz not null,
      profile_id text,
      string_profile_id text,
      broker_client_id text,
      pin jsonb not null default '{}'::jsonb,
      qr_code jsonb not null default '{}'::jsonb,
      attio_id text,
      funnel_id text,
      attio_tour_id text,
      phone text,
      name text,
      stratis_meta jsonb,
      completion_state jsonb,
      utm_source text,
      utm_medium text,
      utm_campaign text,
      utm_content text,
      utm_term text,
      status text default 'booked',
      updated_at timestamptz default now(),
      primary key (id)
    );
    """,
    """
    create table if not exists public.cities (
      id uuid default gen_random_uuid(),
      name text not null,
      state text not null,
      country text not null,
      location text,
      timezone text,
      show_in_onboarding boolean not null default false,
      state_full_name text not null,
      show_in_app boolean not null default true,
      primary key (id)
    );
    """,
    """
    create table if not exists public.feedback (
      id bigint generated always as identity,
      created_at timestamptz not null default now(),
      profile_id uuid,
      raw_feedback jsonb,
      floorplan_id uuid,
      type text,
      booking_id uuid,
      primary key (id)
    );
    """,
    """
    create table if not exists public.dashboard_home_ui (
      id text primary key default 'default',
      copy_json jsonb not null default '{}'::jsonb,
      updated_at timestamptz not null default now()
    );
    """,
    """
    create table if not exists public.floorplans (
      id uuid default gen_random_uuid(),
      created_at timestamptz not null default now(),
      name text not null,
      description text not null default '',
      bedrooms text not null,
      bathrooms text not null,
      half_bathrooms text,
      square_footage text,
      pets_allowed boolean not null default false,
      amenities text[] not null default '{}'::text[],
      tour_id uuid,
      property_id uuid,
      booking_availability text not null default '',
      _num_images bigint not null default 0,
      address jsonb default '{}'::jsonb,
      half_bedrooms text,
      yardi_id text,
      is_convertible boolean not null default false,
      realpage_id text,
      entrata_floorplan_id text,
      visible_override boolean,
      engrain_floor_plan_id text,
      primary key (id)
    );
    """,
    """
    create table if not exists public.properties (
      id uuid default gen_random_uuid(),
      created_at timestamptz not null default now(),
      name text not null,
      description text,
      address jsonb not null,
      latitude double precision,
      longitude double precision,
      units bigint,
      floors bigint,
      neighborhood_id uuid,
      city_id uuid,
      utilities jsonb not null default '{}'::jsonb,
      amenities text[] not null default '{}'::text[],
      fees jsonb[] not null default '{}'::jsonb[],
      _num_images bigint not null default 0,
      website text not null default '',
      attio_list_id text,
      concession text not null default '',
      attio_building_id text,
      payment_model text default 'Subscription',
      timezone text,
      yardi_id text,
      yardi_voyager_server_id uuid,
      funnel_community_id text,
      neighborhood_description text,
      neighborhood_highlights text[],
      realpage_pmcid text,
      realpage_siteid text,
      elise_id text,
      entrata_id text,
      entrata_subdomain text,
      neighborhood_name text,
      realpage_revenue_management_enabled text,
      go_live_date date,
      realpage_knock_id text,
      tours_start_time double precision,
      tours_end_time double precision,
      pmc_id uuid,
      internal_only boolean not null default true,
      min_from_campus text,
      parking jsonb default '[]'::jsonb,
      housing_type text default 'multifamily',
      entrata_housing_type text,
      instagram text,
      year_built integer,
      geo_highlights text[],
      limit_analytics boolean not null default false,
      credit_card_hold_enabled boolean default false,
      credit_card_hold_amount integer default 0,
      pricing_term_strategy text not null default 'global_min',
      pricing_term_months integer,
      requires_id_verification boolean default true,
      gtm_head_script text,
      gtm_body_script text,
      hide_price text not null default '',
      hide_fees boolean not null default false,
      hide_parking_price boolean not null default false,
      tours_type text default 'in_person',
      engrain_embed_id text,
      engrain_origin text,
      engrain_asset_id text,
      engrain_sightmap_id text,
      primary key (id)
    );
    """,
    """
    create table if not exists public.property_images (
      id uuid default gen_random_uuid(),
      property_id uuid not null,
      image_index integer not null,
      image_path text not null,
      created_at timestamptz default now(),
      primary key (id)
    );
    """,
    """
    create table if not exists public.prospect_events (
      id uuid default gen_random_uuid(),
      created_at timestamptz not null default now(),
      property_id text,
      prospect_id text,
      event text not null,
      timestamp timestamptz not null,
      lead_source text not null,
      metadata jsonb not null default '{}'::jsonb,
      ext_event_id text,
      booking_id uuid,
      ignore boolean,
      ignore_dev boolean,
      primary key (id)
    );
    """,
    """
    create table if not exists public.prospects (
      id uuid default gen_random_uuid(),
      created_at timestamptz not null default now(),
      user_id uuid,
      email text,
      phone_number text,
      first_name text,
      last_name text,
      applied boolean default false,
      leased boolean default false,
      ignore boolean default false,
      ignore_dev boolean default false,
      primary key (id)
    );
    """,
    """
    create table if not exists public.spaces (
      id uuid default gen_random_uuid(),
      unit_id text,
      is_affordable boolean,
      has_pricing boolean,
      make_ready_date date,
      availability_status text not null,
      available_date date,
      marketing_unit_number text,
      entrata_space_id text,
      min_rent numeric,
      max_rent numeric,
      min_deposit numeric,
      max_deposit numeric,
      occupancy_type text,
      exclusion_reason text,
      created_at timestamptz default now(),
      updated_at timestamptz default now(),
      rentable boolean default false,
      tourable boolean default false,
      primary key (id)
    );
    """,
    """
    create table if not exists public.tour_steps (
      tour_id uuid,
      title text not null,
      floor bigint,
      type text,
      feedback text,
      unit_id uuid,
      index bigint,
      id uuid default gen_random_uuid(),
      floorplan_id uuid,
      archived_at timestamptz,
      primary key (id)
    );
    """,
    """
    create table if not exists public.tours (
      id uuid default gen_random_uuid(),
      created_at timestamptz not null default now(),
      description text not null default '',
      title text not null default '',
      property_id uuid,
      estimated_minutes bigint not null default 30,
      audio_sync_status text default 'Synced',
      visible boolean not null default true,
      locked_for_sync boolean not null default false,
      tour_concession text,
      archived_at timestamptz,
      primary key (id)
    );
    """,
    """
    create table if not exists public.unit_images (
      id uuid default gen_random_uuid(),
      unit_id uuid,
      image_index integer not null,
      image_path text not null,
      created_at timestamptz default now(),
      updated_at timestamptz default now(),
      primary key (id)
    );
    """,
    """
    create table if not exists public.units (
      id uuid default gen_random_uuid(),
      created_at timestamptz not null default now(),
      property_id uuid,
      description text not null default '',
      unit text not null default '',
      floor text default '',
      monthly_rent bigint,
      move_in_date timestamptz,
      active boolean not null default true,
      floorplan_id uuid,
      view text not null default '',
      lease_months bigint,
      net_effective_rent bigint,
      concession text,
      application_url text,
      num_of_image_views bigint not null default 0,
      yardi_id text,
      device_id text,
      ada_accesible boolean default false,
      pets_allowed boolean default false,
      realpage_id text,
      display_order integer,
      entrata_unit_id text,
      rentable boolean not null default false,
      rentable_override boolean,
      tourable boolean not null default false,
      tourable_override boolean,
      engrain_unit_id text,
      engrain_unit_number text,
      building_number text,
      primary key (id)
    );
    """,
]


def _seed(conn: psycopg.Connection) -> None:
    property_name_pool = [
        "Oak Residences",
        "Skyline Towers",
        "River Lofts",
        "Maple Heights",
        "Cedar Point Apartments",
        "Harbor View Homes",
        "Lakeside Commons",
        "Pine Grove Villas",
        "Grand Central Living",
        "Sunset Ridge",
        "Willow Creek",
        "Parkside Estates",
        "Highland Square",
        "Cityline Residences",
        "Brookstone Flats",
        "Northgate Commons",
        "Elmwood Court",
        "Beacon Hill Towers",
        "The Meridian",
        "Aurora Place",
    ]

    prospect_name_pool = [
        ("Sarah", "Martinez"),
        ("Michael", "Chen"),
        ("Jessica", "Wilson"),
        ("Amanda", "Rodriguez"),
        ("David", "Park"),
        ("Priya", "Sharma"),
        ("Kevin", "Nguyen"),
        ("Emily", "Johnson"),
        ("Noah", "Davis"),
        ("Olivia", "Taylor"),
        ("Ethan", "Brown"),
        ("Sophia", "Anderson"),
        ("Daniel", "Lee"),
        ("Maya", "Patel"),
        ("Ryan", "Garcia"),
        ("Chloe", "White"),
        ("Liam", "Harris"),
        ("Ava", "Clark"),
        ("Benjamin", "Lewis"),
        ("Zoe", "Walker"),
        ("Arjun", "Mehta"),
        ("Nina", "Baker"),
        ("Lucas", "King"),
        ("Grace", "Scott"),
        ("Mateo", "Ramirez"),
        ("Hannah", "Green"),
        ("Owen", "Adams"),
        ("Leah", "Nelson"),
        ("Isaac", "Carter"),
        ("Ruby", "Mitchell"),
        ("Caleb", "Perez"),
        ("Ella", "Roberts"),
        ("Logan", "Turner"),
        ("Ivy", "Phillips"),
        ("Wyatt", "Campbell"),
        ("Aria", "Parker"),
        ("Aiden", "Evans"),
        ("Mila", "Edwards"),
        ("Julian", "Collins"),
        ("Layla", "Stewart"),
    ]

    with conn.cursor() as cur:
        cur.execute("delete from booking_payments")
        cur.execute("delete from feedback")
        cur.execute("delete from prospect_events")
        cur.execute("delete from bookings")
        cur.execute("delete from tour_steps")
        cur.execute("delete from unit_images")
        cur.execute("delete from property_images")
        cur.execute("delete from spaces")
        cur.execute("delete from units")
        cur.execute("delete from floorplans")
        cur.execute("delete from tours")
        cur.execute("delete from prospects")
        cur.execute("delete from properties")
        cur.execute("delete from cities")

        city_ids = [uuid.uuid4() for _ in range(5)]
        for i, city_id in enumerate(city_ids, start=1):
            cur.execute(
                """
                insert into cities (id, name, state, country, state_full_name, timezone, show_in_onboarding, show_in_app)
                values (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (city_id, f"City {i}", "CA", "USA", "California", "America/Los_Angeles", True, True),
            )

        property_ids = [uuid.uuid4() for _ in range(20)]
        for i, pid in enumerate(property_ids, start=1):
            property_name = property_name_pool[(i - 1) % len(property_name_pool)]
            cur.execute(
                """
                insert into properties (
                  id, name, description, address, latitude, longitude, units, floors, city_id, amenities, fees,
                  website, concession, payment_model, timezone, neighborhood_name, go_live_date, tours_start_time,
                  tours_end_time, internal_only, housing_type, year_built, pricing_term_strategy, hide_price
                )
                values (
                  %s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s::text[],%s::jsonb[],%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    pid,
                    property_name,
                    "Seeded property for dashboard APIs",
                    '{"line1":"100 Main St","city":"City","state":"CA","zip":"90000"}',
                    34.0 + (i * 0.01),
                    -118.0 - (i * 0.01),
                    200 + i,
                    5 + (i % 10),
                    city_ids[i % len(city_ids)],
                    ["gym", "pool"],
                    ['{"name":"application_fee","amount":50}'],
                    f"https://property{i}.example.com",
                    "1 month free",
                    "Subscription",
                    "America/Los_Angeles",
                    f"District {i}",
                    date.today() - timedelta(days=i),
                    9.0,
                    18.0,
                    False,
                    "multifamily",
                    2000 + (i % 20),
                    "global_min",
                    "",
                ),
            )
            cur.execute(
                "insert into property_images (property_id, image_index, image_path) values (%s,%s,%s)",
                (pid, 1, f"/images/properties/{i}.jpg"),
            )

        tour_ids = [uuid.uuid4() for _ in range(20)]
        for i, tid in enumerate(tour_ids, start=1):
            cur.execute(
                """
                insert into tours (id, title, description, property_id, estimated_minutes, audio_sync_status, visible, locked_for_sync, tour_concession)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    tid,
                    f"Tour {i}",
                    "Seeded guided tour",
                    property_ids[i % len(property_ids)],
                    30,
                    "Synced",
                    True,
                    False,
                    "No concession",
                ),
            )

        floorplan_ids = [uuid.uuid4() for _ in range(40)]
        for i, fid in enumerate(floorplan_ids, start=1):
            cur.execute(
                """
                insert into floorplans (id, name, description, bedrooms, bathrooms, square_footage, pets_allowed, amenities, tour_id, property_id, booking_availability, address)
                values (%s,%s,%s,%s,%s,%s,%s,%s::text[],%s,%s,%s,%s::jsonb)
                """,
                (
                    fid,
                    f"FP-{i}",
                    "Seeded floorplan",
                    str(1 + (i % 3)),
                    str(1 + (i % 2)),
                    str(700 + i * 5),
                    True,
                    ["balcony", "washer"],
                    tour_ids[i % len(tour_ids)],
                    property_ids[i % len(property_ids)],
                    "available",
                    '{"line1":"100 Main St"}',
                ),
            )

        unit_ids = [uuid.uuid4() for _ in range(60)]
        for i, uid in enumerate(unit_ids, start=1):
            cur.execute(
                """
                insert into units (
                  id, property_id, description, unit, floor, monthly_rent, move_in_date, active, floorplan_id, view,
                  lease_months, net_effective_rent, application_url, rentable, tourable
                )
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    uid,
                    property_ids[i % len(property_ids)],
                    "Seeded unit",
                    f"A-{100+i}",
                    str((i % 10) + 1),
                    1400 + (i * 10),
                    datetime.now(UTC) + timedelta(days=i),
                    True,
                    floorplan_ids[i % len(floorplan_ids)],
                    "city",
                    12,
                    1300 + (i * 8),
                    f"https://apply.example.com/unit/{i}",
                    True,
                    True,
                ),
            )
            cur.execute(
                """
                insert into spaces (
                  unit_id, is_affordable, has_pricing, make_ready_date, availability_status, available_date,
                  marketing_unit_number, min_rent, max_rent, min_deposit, max_deposit, occupancy_type, rentable, tourable
                )
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    str(uid),
                    i % 4 == 0,
                    True,
                    date.today() + timedelta(days=i),
                    "available" if i % 5 else "notice",
                    date.today() + timedelta(days=i + 3),
                    f"M-{i}",
                    Decimal(1200 + i * 5),
                    Decimal(1500 + i * 5),
                    Decimal(300),
                    Decimal(500),
                    "market",
                    True,
                    True,
                ),
            )
            cur.execute(
                "insert into unit_images (unit_id, image_index, image_path) values (%s,%s,%s)",
                (uid, 1, f"/images/units/{i}.jpg"),
            )

        prospect_ids = [uuid.uuid4() for _ in range(40)]
        for i, prid in enumerate(prospect_ids, start=1):
            first_name, last_name = prospect_name_pool[(i - 1) % len(prospect_name_pool)]
            cur.execute(
                """
                insert into prospects (id, email, phone_number, first_name, last_name, applied, leased, ignore, ignore_dev)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    prid,
                    f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                    f"+1555000{i:04d}",
                    first_name,
                    last_name,
                    i % 3 == 0,
                    i % 8 == 0,
                    False,
                    False,
                ),
            )

            cur.execute(
                """
                insert into prospect_events (property_id, prospect_id, event, timestamp, lead_source, metadata, ext_event_id, ignore, ignore_dev)
                values (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s)
                """,
                (
                    str(property_ids[i % len(property_ids)]),
                    str(prid),
                    random.choice(["tour_booked", "message_sent", "application_started"]),
                    datetime.now(UTC) - timedelta(hours=i),
                    random.choice(["website", "google_ads", "referral"]),
                    '{"channel":"sms"}',
                    f"ext-{i}",
                    False,
                    False,
                ),
            )

        booking_ids = [uuid.uuid4() for _ in range(30)]
        for i, bid in enumerate(booking_ids, start=1):
            start = datetime.now(UTC) + timedelta(days=i)
            end = start + timedelta(minutes=45)
            cur.execute(
                """
                insert into bookings (
                  id, floorplan_id, start_time, end_time, profile_id, string_profile_id, phone, name,
                  stratis_meta, completion_state, utm_source, utm_medium, utm_campaign, utm_content, utm_term, status
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s)
                """,
                (
                    bid,
                    str(floorplan_ids[i % len(floorplan_ids)]),
                    start,
                    end,
                    str(prospect_ids[i % len(prospect_ids)]),
                    str(prospect_ids[i % len(prospect_ids)]),
                    f"+1555000{i:04d}",
                    f"{first_name} {last_name}",
                    '{"source":"seed"}',
                    '{"state":"completed"}',
                    "google",
                    "cpc",
                    "spring_campaign",
                    "ad_copy_a",
                    "apartments",
                    "booked",
                ),
            )
            cur.execute(
                """
                insert into booking_payments (booking_id, property_id, payment_intent_id, collateral_amount, payment_status, captured_amount, profile_id)
                values (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    str(bid),
                    str(property_ids[i % len(property_ids)]),
                    f"pi_{i:04d}",
                    "500",
                    "captured" if i % 2 == 0 else "pending",
                    500 if i % 2 == 0 else 0,
                    prospect_ids[i % len(prospect_ids)],
                ),
            )

            cur.execute(
                """
                insert into feedback (profile_id, raw_feedback, floorplan_id, type, booking_id)
                values (%s,%s::jsonb,%s,%s,%s)
                """,
                (
                    prospect_ids[i % len(prospect_ids)],
                    '{"rating":4,"notes":"Great tour flow"}',
                    floorplan_ids[i % len(floorplan_ids)],
                    "tour_feedback",
                    bid,
                    ),
                )

        # Per-floorplan unit feedback (inventory detail popup shows last 5 by floorplan_id).
        _unit_fb_templates: list[dict] = [
            {
                "rating": 4,
                "notes": "Liked layout; comparing to one other community this week.",
                "likes": ["Open kitchen", "Balcony size"],
                "improvements": [],
            },
            {
                "rating": 3,
                "notes": "Concerned about natural light in the main living area.",
                "likes": ["Bedroom dimensions"],
                "improvements": ["Brightness in living room", "Closet depth"],
            },
            {
                "rating": 5,
                "notes": "Strong interest — requested pricing on shorter lease term.",
                "likes": ["Finishes", "Noise level"],
                "improvements": [],
            },
            {
                "rating": 2,
                "notes": "Bathroom felt tight vs expectations from photos.",
                "likes": ["Location"],
                "improvements": ["Bathroom layout", "Storage"],
            },
            {
                "rating": 4,
                "notes": "Would revisit if similar unit on higher floor becomes available.",
                "likes": ["View from bedroom"],
                "improvements": ["Elevator wait at peak"],
            },
        ]
        for fp_idx, fpid in enumerate(floorplan_ids):
            for j in range(5):
                tpl = _unit_fb_templates[j % len(_unit_fb_templates)]
                created = datetime.now(UTC) - timedelta(days=j * 4 + (fp_idx % 5), hours=(fp_idx + j * 3) % 20)
                pr = prospect_ids[(fp_idx * 7 + j * 3) % len(prospect_ids)]
                cur.execute(
                    """
                    insert into feedback (profile_id, raw_feedback, floorplan_id, type, booking_id, created_at)
                    values (%s,%s::jsonb,%s,%s,%s,%s)
                    """,
                    (str(pr), json.dumps(tpl), str(fpid), "Unit", None, created),
                )

        for i, tid in enumerate(tour_ids, start=1):
            for j in range(1, 3):
                cur.execute(
                    """
                    insert into tour_steps (tour_id, title, floor, type, feedback, unit_id, index, floorplan_id)
                    values (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        tid,
                        f"Step {j} for tour {i}",
                        j,
                        "unit",
                        "Looks good",
                        unit_ids[(i + j) % len(unit_ids)],
                        j,
                        floorplan_ids[(i + j) % len(floorplan_ids)],
                    ),
                )


def main() -> None:
    db_url = _require_db_url()
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            for ddl in DDL_STATEMENTS:
                cur.execute(ddl)
        _seed(conn)
    print("Bootstrap complete: tables created and data seeded.")


if __name__ == "__main__":
    main()
