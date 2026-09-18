-- ============================================================================
-- Migration: 001_initial_schema.sql
-- Description: Core schema for Money Docs Decoded matching 05-database-schema.md
-- Engine: Supabase / PostgreSQL with pgvector extension
-- ============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    plan_tier TEXT NOT NULL DEFAULT 'free' CHECK (plan_tier IN ('free', 'paid')),
    preferred_language TEXT NOT NULL DEFAULT 'en',
    data_retention_opt_in BOOLEAN NOT NULL DEFAULT FALSE
);

-- 3. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN ('health_insurance', 'loan', 'mutual_fund')),
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'extracted', 'chunked', 'embedded', 'analyzed', 'failed')),
    issuer_name TEXT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL
);

-- 4. Document Chunks Table (Vector Store for RAG)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    clause_label TEXT NULL,
    text TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Document Summaries Table
CREATE TABLE IF NOT EXISTS document_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    language TEXT NOT NULL DEFAULT 'en',
    coverage JSONB NOT NULL DEFAULT '[]'::jsonb,
    exclusions JSONB NOT NULL DEFAULT '[]'::jsonb,
    key_fees JSONB NOT NULL DEFAULT '[]'::jsonb,
    waiting_periods JSONB NOT NULL DEFAULT '[]'::jsonb,
    notable_terms JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_version TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_summary_lang UNIQUE (document_id, language)
);

-- 6. Red-Flag Patterns Table (The Ombudsman Knowledge Base)
CREATE TABLE IF NOT EXISTS red_flag_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL,
    clause_type TEXT NOT NULL,
    trigger_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    trigger_regex TEXT NULL,
    plain_explanation_template TEXT NOT NULL,
    severity_default TEXT NOT NULL CHECK (severity_default IN ('high', 'medium', 'low')),
    source_reference TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Red Flags Table (Detected Flags per Document)
CREATE TABLE IF NOT EXISTS red_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    pattern_id UUID NULL REFERENCES red_flag_patterns(id) ON DELETE SET NULL,
    chunk_id UUID NULL REFERENCES document_chunks(id) ON DELETE SET NULL,
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    plain_explanation TEXT NOT NULL,
    confirmed_by_llm BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Confidence Scores Table
CREATE TABLE IF NOT EXISTS confidence_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    breakdown JSONB NOT NULL DEFAULT '[]'::jsonb,
    kb_version TEXT NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Chat Messages Table (Conversational Q&A History)
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    cited_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. Benchmark Products Table (Public Scraped Policies & Market Intelligence)
CREATE TABLE IF NOT EXISTS benchmark_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_category TEXT NOT NULL,
    issuer_name TEXT NOT NULL,
    product_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    complaint_signal JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. Scrape Jobs Table (n8n Webhook & Worker Execution Logs)
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'success', 'failed', 'skipped_robots')),
    triggered_by TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ NULL,
    error_message TEXT NULL
);

-- ============================================================================
-- Performance & Query Indices
-- ============================================================================

-- Vector similarity search index (HNSW cosine ops)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
    ON document_chunks 
    USING hnsw (embedding vector_cosine_ops);

-- Benchmark product category & issuer composite search
CREATE INDEX IF NOT EXISTS idx_benchmark_products_category_issuer 
    ON benchmark_products (product_category, issuer_name);

-- Admin / pipeline health queries
CREATE INDEX IF NOT EXISTS idx_documents_status 
    ON documents (status);

-- Foreign key lookup indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id 
    ON documents (user_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id 
    ON document_chunks (document_id);

CREATE INDEX IF NOT EXISTS idx_red_flags_document_id 
    ON red_flags (document_id);

CREATE INDEX IF NOT EXISTS idx_confidence_scores_document_id 
    ON confidence_scores (document_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_document_id 
    ON chat_messages (document_id);
