# Data Layer — Component Spec

**Role:** Single source of truth for users, documents, extracted content, analysis results, the red-flag knowledge base, and scraped benchmark data. Recommendation: **Postgres with the `pgvector` extension** (Supabase).

## Core tables (conceptual, not final DDL)

### `users`
`id, email, created_at, plan_tier (free|paid), preferred_language, data_retention_opt_in`

### `documents`
`id, user_id, filename, document_type (health_insurance|loan|mutual_fund), storage_path, status (uploaded|extracted|chunked|embedded|analyzed|failed), issuer_name (nullable, detected or user-provided), uploaded_at, deleted_at (soft delete for DPDP "right to erasure")`

### `document_chunks`
`id, document_id, page_number, clause_label (nullable), text, embedding (vector), created_at`
- Indexed with an IVFFlat/HNSW index on `embedding` for fast similarity search.

### `document_summaries`
`id, document_id, language, coverage (jsonb), exclusions (jsonb), key_fees (jsonb), waiting_periods (jsonb), notable_terms (jsonb), model_version, generated_at`
- Cached per document+language so repeat views don't re-call the LLM.

### `red_flags`
`id, document_id, pattern_id (fk → red_flag_patterns), chunk_id (fk → document_chunks), severity, plain_explanation, confirmed_by_llm (bool), created_at`

### `red_flag_patterns` (the Knowledge Base)
`id, category, clause_type, trigger_keywords (jsonb), trigger_regex (nullable), plain_explanation_template, severity_default, source_reference, created_at, updated_at`

### `confidence_scores`
`id, document_id, score, breakdown (jsonb — list of {reason, points}), kb_version, computed_at`

### `chat_messages`
`id, document_id, user_id, role (user|assistant), content, cited_chunk_ids (jsonb), created_at`

### `benchmark_products` (from the scraping component)
`id, product_category, issuer_name, product_name, source_url, attributes (jsonb), complaint_signal (jsonb), last_scraped_at`

### `scrape_jobs`
`id, source_url, status (pending|success|failed|skipped_robots), triggered_by (n8n workflow id), started_at, finished_at, error_message`

## Storage layer

- **Object storage** (S3-compatible / Supabase Storage): raw uploaded PDFs and images. Never store raw files in Postgres.
- **Retention policy:** raw files + extracted text deletable on user request (`DELETE /documents/{id}`) — cascade-delete chunks, summaries, red flags, chat history. This is required for DPDP Act ("right to erasure") compliance, not optional polish.

## Indexing & performance notes

- Vector index on `document_chunks.embedding` — required for the Q&A RAG lookup to stay fast as documents grow.
- Composite index on `benchmark_products(product_category, issuer_name)` for fast compare-page lookups.
- `documents.status` should be indexed if you build the admin/monitoring dashboard, since it'll be queried frequently to show pipeline health.

## Data classification (important for security posture, see `07-infra-deployment-security.md`)

| Data | Sensitivity | Notes |
|---|---|---|
| Raw uploaded documents | High (may contain health/financial PII) | Encrypt at rest, access-controlled by `user_id` |
| Document chunks/embeddings | High | Same as above — embeddings can leak content if the vector DB is exposed |
| Chat history | High | Contains user's own questions about personal finances/health |
| Red-flag KB | Low | Not user-specific, safe to expose more broadly (even could be a public API later) |
| Benchmark products | Low | Public data by construction |