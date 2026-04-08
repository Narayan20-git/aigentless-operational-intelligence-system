-- ============================================================
-- Aigentless POC — Category 2 Migration
-- 7 new tables for Property Onboarding screen
-- All reference public.properties(id) via FK
-- Run this in Supabase SQL Editor
-- ============================================================

-- Enable pgvector extension (needed for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- TABLE 1: property_onboarding_status
-- One record per property — overall completeness + status
-- Powers the KPI cards and status badges in the UI
-- ============================================================
CREATE TABLE IF NOT EXISTS public.property_onboarding_status (
  id                    uuid NOT NULL DEFAULT gen_random_uuid(),
  property_id           uuid NOT NULL,
  overall_completeness  integer NOT NULL DEFAULT 0
                        CHECK (overall_completeness >= 0 AND overall_completeness <= 100),
  status                text NOT NULL DEFAULT 'in-progress'
                        CHECK (status IN ('ready', 'in-progress', 'blocked')),
  last_calculated_at    timestamp with time zone DEFAULT now(),
  created_at            timestamp with time zone NOT NULL DEFAULT now(),
  updated_at            timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT property_onboarding_status_pkey PRIMARY KEY (id),
  CONSTRAINT property_onboarding_status_property_id_key UNIQUE (property_id),
  CONSTRAINT property_onboarding_status_property_id_fkey
    FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 2: property_onboarding_sections
-- 6 section records per property (60 total for 10 properties)
-- Sections: property_info | units_floor_plans | amenities |
--           media_photos  | content_faqs | integrations
-- Powers the section progress bars in the right panel
-- ============================================================
CREATE TABLE IF NOT EXISTS public.property_onboarding_sections (
  id              uuid NOT NULL DEFAULT gen_random_uuid(),
  property_id     uuid NOT NULL,
  section         text NOT NULL
                  CHECK (section IN (
                    'property_info', 'units_floor_plans', 'amenities',
                    'media_photos',  'content_faqs',       'integrations'
                  )),
  completion_pct  integer NOT NULL DEFAULT 0
                  CHECK (completion_pct >= 0 AND completion_pct <= 100),
  status          text NOT NULL DEFAULT 'not-started'
                  CHECK (status IN ('complete', 'in-progress', 'not-started', 'blocked')),
  metadata        jsonb DEFAULT '{}'::jsonb,
  created_at      timestamp with time zone NOT NULL DEFAULT now(),
  updated_at      timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT property_onboarding_sections_pkey PRIMARY KEY (id),
  CONSTRAINT property_onboarding_sections_unique UNIQUE (property_id, section),
  CONSTRAINT property_onboarding_sections_property_id_fkey
    FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 3: property_onboarding_blockers
-- Blocker records per property
-- Powers the blockers panel and warning messages in the UI
-- ============================================================
CREATE TABLE IF NOT EXISTS public.property_onboarding_blockers (
  id           uuid NOT NULL DEFAULT gen_random_uuid(),
  property_id  uuid NOT NULL,
  section      text NOT NULL
               CHECK (section IN (
                 'property_info', 'units_floor_plans', 'amenities',
                 'media_photos',  'content_faqs',       'integrations'
               )),
  type         text NOT NULL
               CHECK (type IN (
                 'missing_content', 'sync_pending',
                 'missing_media',   'incomplete_info', 'no_data'
               )),
  severity     text NOT NULL DEFAULT 'warning'
               CHECK (severity IN ('blocking', 'warning', 'info')),
  message      text NOT NULL,
  description  text,
  action       text,
  ai_can_fix   boolean NOT NULL DEFAULT false,
  resolved     boolean NOT NULL DEFAULT false,
  resolved_at  timestamp with time zone,
  created_at   timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT property_onboarding_blockers_pkey PRIMARY KEY (id),
  CONSTRAINT property_onboarding_blockers_property_id_fkey
    FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 4: property_faqs
-- Structured Q&A pairs per property
-- Created manually or via AI "Generate missing content" button
-- ============================================================
CREATE TABLE IF NOT EXISTS public.property_faqs (
  id            uuid NOT NULL DEFAULT gen_random_uuid(),
  property_id   uuid NOT NULL,
  question      text NOT NULL,
  answer        text NOT NULL DEFAULT '',
  category      text NOT NULL DEFAULT 'general'
                CHECK (category IN (
                  'general', 'pet_policy', 'parking',
                  'utilities', 'lease', 'maintenance',
                  'guest', 'noise', 'move_in', 'move_out'
                )),
  ai_generated  boolean NOT NULL DEFAULT false,
  is_published  boolean NOT NULL DEFAULT false,
  embedding     vector(768),
  created_at    timestamp with time zone NOT NULL DEFAULT now(),
  updated_at    timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT property_faqs_pkey PRIMARY KEY (id),
  CONSTRAINT property_faqs_property_id_fkey
    FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 5: property_amenities
-- Structured amenities with descriptions per property
-- Extends the simple text[] array in properties table
-- ============================================================
CREATE TABLE IF NOT EXISTS public.property_amenities (
  id            uuid NOT NULL DEFAULT gen_random_uuid(),
  property_id   uuid NOT NULL,
  name          text NOT NULL,
  description   text NOT NULL DEFAULT '',
  category      text NOT NULL DEFAULT 'general'
                CHECK (category IN (
                  'outdoor', 'indoor', 'pet',
                  'parking', 'tech', 'wellness', 'general'
                )),
  ai_generated  boolean NOT NULL DEFAULT false,
  embedding     vector(768),
  created_at    timestamp with time zone NOT NULL DEFAULT now(),
  updated_at    timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT property_amenities_pkey PRIMARY KEY (id),
  CONSTRAINT property_amenities_property_id_fkey
    FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 6: property_ai_content_jobs
-- Tracks every "Generate missing content" button click
-- Async job tracking: pending → running → completed/failed
-- ============================================================
CREATE TABLE IF NOT EXISTS public.property_ai_content_jobs (
  id                 uuid NOT NULL DEFAULT gen_random_uuid(),
  property_id        uuid NOT NULL,
  section            text NOT NULL
                     CHECK (section IN (
                       'property_info', 'units_floor_plans', 'amenities',
                       'media_photos',  'content_faqs',       'integrations'
                     )),
  content_type       text NOT NULL
                     CHECK (content_type IN (
                       'faq', 'amenity_description', 'property_description'
                     )),
  status             text NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  prompt_used        text,
  generated_content  jsonb,
  error_message      text,
  triggered_by       text,
  created_at         timestamp with time zone NOT NULL DEFAULT now(),
  completed_at       timestamp with time zone,
  CONSTRAINT property_ai_content_jobs_pkey PRIMARY KEY (id),
  CONSTRAINT property_ai_content_jobs_property_id_fkey
    FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 7: property_integration_status
-- Unified integration connection status per property
-- Powers the Integrations section in onboarding
-- ============================================================
CREATE TABLE IF NOT EXISTS public.property_integration_status (
  id                uuid NOT NULL DEFAULT gen_random_uuid(),
  property_id       uuid NOT NULL,
  integration_name  text NOT NULL
                    CHECK (integration_name IN (
                      'yardi', 'apartments_com',
                      'zillow', 'rent_com', 'appfolio'
                    )),
  category          text NOT NULL DEFAULT 'lead_sources'
                    CHECK (category IN (
                      'property_management', 'lead_sources', 'marketing'
                    )),
  status            text NOT NULL DEFAULT 'not_connected'
                    CHECK (status IN ('connected', 'not_connected', 'error')),
  last_sync_at      timestamp with time zone,
  daily_api_calls   integer NOT NULL DEFAULT 0,
  daily_api_limit   integer NOT NULL DEFAULT 1000,
  error_message     text,
  created_at        timestamp with time zone NOT NULL DEFAULT now(),
  updated_at        timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT property_integration_status_pkey PRIMARY KEY (id),
  CONSTRAINT property_integration_status_unique UNIQUE (property_id, integration_name),
  CONSTRAINT property_integration_status_property_id_fkey
    FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE
);

-- ============================================================
-- INDEXES — for fast queries on commonly filtered columns
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_onboarding_status_property
  ON public.property_onboarding_status(property_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_status_status
  ON public.property_onboarding_status(status);

CREATE INDEX IF NOT EXISTS idx_onboarding_sections_property
  ON public.property_onboarding_sections(property_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_sections_section
  ON public.property_onboarding_sections(section);

CREATE INDEX IF NOT EXISTS idx_onboarding_blockers_property
  ON public.property_onboarding_blockers(property_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_blockers_resolved
  ON public.property_onboarding_blockers(resolved);
CREATE INDEX IF NOT EXISTS idx_onboarding_blockers_severity
  ON public.property_onboarding_blockers(severity);

CREATE INDEX IF NOT EXISTS idx_property_faqs_property
  ON public.property_faqs(property_id);
CREATE INDEX IF NOT EXISTS idx_property_faqs_category
  ON public.property_faqs(category);
CREATE INDEX IF NOT EXISTS idx_property_faqs_published
  ON public.property_faqs(is_published);

CREATE INDEX IF NOT EXISTS idx_property_amenities_property
  ON public.property_amenities(property_id);
CREATE INDEX IF NOT EXISTS idx_property_amenities_category
  ON public.property_amenities(category);

CREATE INDEX IF NOT EXISTS idx_ai_jobs_property
  ON public.property_ai_content_jobs(property_id);
CREATE INDEX IF NOT EXISTS idx_ai_jobs_status
  ON public.property_ai_content_jobs(status);

CREATE INDEX IF NOT EXISTS idx_integration_status_property
  ON public.property_integration_status(property_id);
CREATE INDEX IF NOT EXISTS idx_integration_status_status
  ON public.property_integration_status(status);

-- Vector similarity search indexes (for embeddings)
CREATE INDEX IF NOT EXISTS idx_faqs_embedding
  ON public.property_faqs USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_amenities_embedding
  ON public.property_amenities USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- ============================================================
-- HELPER FUNCTION: recalculate_onboarding_status()
-- Called by FastAPI scheduled job every 5 minutes
-- Updates overall_completeness and status for a property
-- ============================================================
CREATE OR REPLACE FUNCTION public.recalculate_onboarding_status(p_property_id uuid)
RETURNS void AS $$
DECLARE
  v_avg_pct   integer;
  v_status    text;
  v_blocked   boolean;
BEGIN
  -- Calculate average completion across all 6 sections
  SELECT COALESCE(AVG(completion_pct)::integer, 0)
  INTO v_avg_pct
  FROM public.property_onboarding_sections
  WHERE property_id = p_property_id;

  -- Check if any blocking blockers exist
  SELECT EXISTS (
    SELECT 1 FROM public.property_onboarding_blockers
    WHERE property_id = p_property_id
      AND severity = 'blocking'
      AND resolved = false
  ) INTO v_blocked;

  -- Determine status
  IF v_blocked THEN
    v_status := 'blocked';
  ELSIF v_avg_pct = 100 THEN
    v_status := 'ready';
  ELSE
    v_status := 'in-progress';
  END IF;

  -- Upsert into property_onboarding_status
  INSERT INTO public.property_onboarding_status
    (property_id, overall_completeness, status, last_calculated_at, updated_at)
  VALUES
    (p_property_id, v_avg_pct, v_status, now(), now())
  ON CONFLICT (property_id)
  DO UPDATE SET
    overall_completeness = EXCLUDED.overall_completeness,
    status               = EXCLUDED.status,
    last_calculated_at   = EXCLUDED.last_calculated_at,
    updated_at           = EXCLUDED.updated_at;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SUCCESS MESSAGE
-- ============================================================
DO $$
BEGIN
  RAISE NOTICE '✅ Migration complete! 7 new tables created with FK to properties.';
  RAISE NOTICE '   Tables: property_onboarding_status, property_onboarding_sections,';
  RAISE NOTICE '           property_onboarding_blockers, property_faqs,';
  RAISE NOTICE '           property_amenities, property_ai_content_jobs,';
  RAISE NOTICE '           property_integration_status';
  RAISE NOTICE '   pgvector enabled for embeddings on faqs + amenities';
END $$;
