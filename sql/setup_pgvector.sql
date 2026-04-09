-- ============================================================
-- pgvector Setup for Supabase
-- Enables semantic search for RAG in Generate Missing Content
-- Run this in Supabase SQL Editor AFTER migration_category2.sql
-- ============================================================

-- Enable pgvector (already in migration but safe to re-run)
CREATE EXTENSION IF NOT EXISTS vector;

-- ── VECTOR SIMILARITY SEARCH FUNCTION ───────────────────────
-- Used by FastAPI to find similar FAQs for RAG context
CREATE OR REPLACE FUNCTION public.match_similar_faqs(
  query_embedding  vector(768),
  match_threshold  float    DEFAULT 0.7,
  match_count      int      DEFAULT 5,
  exclude_prop_id  uuid     DEFAULT NULL
)
RETURNS TABLE (
  id           uuid,
  property_id  uuid,
  question     text,
  answer       text,
  category     text,
  similarity   float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    f.id,
    f.property_id,
    f.question,
    f.answer,
    f.category,
    1 - (f.embedding <=> query_embedding) AS similarity
  FROM public.property_faqs f
  WHERE f.embedding IS NOT NULL
    AND f.is_published = TRUE
    AND f.answer != ''
    AND (exclude_prop_id IS NULL OR f.property_id != exclude_prop_id)
    AND 1 - (f.embedding <=> query_embedding) > match_threshold
  ORDER BY f.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ── SIMILAR AMENITY DESCRIPTIONS ────────────────────────────
CREATE OR REPLACE FUNCTION public.match_similar_amenities(
  query_embedding  vector(768),
  match_threshold  float DEFAULT 0.7,
  match_count      int   DEFAULT 5,
  exclude_prop_id  uuid  DEFAULT NULL
)
RETURNS TABLE (
  id           uuid,
  property_id  uuid,
  name         text,
  description  text,
  category     text,
  similarity   float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    a.id,
    a.property_id,
    a.name,
    a.description,
    a.category,
    1 - (a.embedding <=> query_embedding) AS similarity
  FROM public.property_amenities a
  WHERE a.embedding IS NOT NULL
    AND a.description != ''
    AND (exclude_prop_id IS NULL OR a.property_id != exclude_prop_id)
    AND 1 - (a.embedding <=> query_embedding) > match_threshold
  ORDER BY a.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
