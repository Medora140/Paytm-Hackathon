-- ============================================================================
-- Migration: 002_vector_search_function.sql
-- Description: RPC function for pgvector similarity search on document_chunks
-- ============================================================================

CREATE OR REPLACE FUNCTION match_document_chunks (
  query_embedding vector(384),
  match_count int DEFAULT 5,
  filter_document_id uuid DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  page_number int,
  clause_label text,
  text text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.page_number,
    dc.clause_label,
    dc.text,
    (1 - (dc.embedding <=> query_embedding))::float AS similarity
  FROM document_chunks dc
  WHERE filter_document_id IS NULL OR dc.document_id = filter_document_id
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
