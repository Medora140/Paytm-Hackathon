# Progress — Track 1: Database Schema & Persistence (Gen 2)

Last visited: 2026-09-18T11:41:00Z
Status: EXECUTING_MIGRATION

## Completed Steps
- [x] Initialized Track 1 Gen 2 workspace and BRIEFING.md.
- [x] Read DISPATCH.md, ORIGINAL_REQUEST.md, docs/database.md, and backend/migrations/001_initial_schema.sql.
- [x] Inspected backend/.env credentials:
  - SUPABASE_URL=https://qtcncebuochelpgwqthx.supabase.co
  - SUPABASE_ANON_KEY present
  - SUPABASE_SERVICE_ROLE_KEY present
- [x] Verified live Supabase PostgREST status:
  - Confirmed all required tables currently return PGRST205 (missing in schema cache).
- [x] Confirmed network connectivity:
  - `aws-0-ap-northeast-1.pooler.supabase.com:5432` is reachable (Tokyo pooler).
  - `aws-0-ap-northeast-1.pooler.supabase.com:6543` is reachable.

## Current Step
- Executing SQL migration against live Supabase project `qtcncebuochelpgwqthx`.

## Next Steps
- Verify all 8 tables (+ users and document_summaries) return 200 OK via Supabase client.
- Update `backend/app/ingestion/repository.py` to remove in-memory dict fallbacks.
- Ingest real document through API and verify chunks in `document_chunks`.
- Restart backend process, verify chunks remain directly queryable without re-upload.
- Document verification output and complete handoff.md.
