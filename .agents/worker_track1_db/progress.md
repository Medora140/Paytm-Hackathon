# Progress — Track 1: Database Schema & Persistence

Last visited: 2026-09-18T11:31:00Z
Status: BLOCKED_ON_MIGRATION_EXECUTION

## Completed Steps
- [x] Read DISPATCH.md and ORIGINAL_REQUEST.md.
- [x] Examined database.md and verified backend/migrations/001_initial_schema.sql matches all 8 required tables + pgvector + users + document_summaries + indices.
- [x] Probed live Supabase project (qtcncebuochelpgwqthx.supabase.co):
  - PostgREST endpoint is 200 OK.
  - Confirmed all tables (documents, document_chunks, red_flags, etc.) return HTTP 404 (PGRST205 - not found in schema cache).
  - Identified project region: Tokyo (`ap-northeast-1`).
  - Pooler connectivity confirmed at `aws-0-ap-northeast-1.pooler.supabase.com:5432`.
- [x] Eliminated repository in-memory bypasses in `backend/app/ingestion/repository.py` and `backend/app/scraping/repository.py`.
- [x] Tested Supabase pooler authentication:
  - Connecting via `psycopg2` requires the postgres user password, which is not present in `.env`.
  - Tested `npx supabase db query --linked --project-ref qtcncebuochelpgwqthx`, which requires `SUPABASE_ACCESS_TOKEN`.
- [x] Prepared Windows clipboard with raw `001_initial_schema.sql` and launched browser to `https://supabase.com/dashboard/project/qtcncebuochelpgwqthx/sql/new`.

## Current Focus / Blocker
- Migration DDL requires execution via Supabase SQL Editor or a valid `DATABASE_URL` / `SUPABASE_ACCESS_TOKEN`.
- `001_initial_schema.sql` is currently sitting in the Windows clipboard ready to paste into the open SQL Editor tab, or database password needs to be added to `DATABASE_URL` in `.env`.

## Next Steps Immediately Upon Schema Execution
1. Verify all 8 tables return 200 OK via Supabase client direct query script.
2. Ingest real document through API and verify chunks in `document_chunks`.
3. Kill and restart backend process; verify chunks remain directly queryable without re-upload.
4. Output verification log and handoff.md.
