# DISPATCH — Track 1: Database Schema & Persistence (Gen 2 Replacement)

## Task Objective
You are Worker 1 Gen 2 (Database Schema & Persistence Specialist) for "Money Docs Decoded", replacing the predecessor who hung on a long TCP connection to Supabase pooler.
Your assigned working directory is:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track1_db_gen2

You MUST read the authoritative request file before starting:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\ORIGINAL_REQUEST.md
Also read:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\database.md (exact table definitions — the source of truth)
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\backend\migrations\001_initial_schema.sql
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track1_db\progress.md (predecessor state)
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\backend\.env

## Scope & File Ownership
You exclusively own:
- Supabase project state
- migrations/ directory and migration scripts
- backend/app/ingestion/repository.py (removing in-memory bypasses so queries use Supabase)

## Detailed Requirements
1. Apply the COMPLETE migration from database.md against the real Supabase project (host: qtcncebuochelpgwqthx.supabase.co).
   Every table must exist in public schema:
   - documents
   - document_chunks
   - red_flags
   - red_flag_patterns
   - confidence_scores
   - chat_messages
   - benchmark_products
   - scrape_jobs
2. CAUTION ON NETWORK/CONNECTION:
   - Check what credentials exist in `.env` (e.g. SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL / DB password if present).
   - If running scripts with psycopg2/asyncpg/sqlalchemy, always set a connect_timeout (e.g. 5 seconds) to avoid hanging forever.
   - If direct Postgres port 5432/6543 connection is firewalled or requires a password not in .env, check if Supabase Management API or rpc/sql endpoint or supabase-py with service role key can be used, or check if supabase CLI / access token exists in environment.
3. Confirm via direct query (direct SQL or direct Supabase client query, NOT through the app UI) that EVERY single table exists and is queryable.
4. Remove the repository in-memory cache bypass in `backend/app/ingestion/repository.py` where in-memory dictionary `self._chunks` and `self._documents` were read instead of querying Supabase.
5. Criterion:
   - A document uploaded through real API has its chunks visible via direct Supabase query.
   - Chunks REMAIN visible after a full backend process restart (kill & restart server, then query again without re-uploading).
   - Document the exact query commands and outputs proving persistence.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. An auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Reporting
- Keep progress.md updated in your working directory.
- When finished, write a complete handoff.md in your working directory.
- Send a completion message via send_message to orchestrator conversation ID: b60453ca-e885-497d-b03a-0a1263a67b95.

## 2026-09-18T11:40:12Z
**Context**: Track 1 Gen 2 (Database Schema Worker) Status Check
**Content**: Heartbeat tick 6 check-in. Checking on your initialization and Supabase migration progress. Have you inspected the database connection settings in backend/.env?
**Action**: Please initialize your progress.md and update it with your current step and findings.

## 2026-09-18T11:55:25Z
**Context**: Track 1 Database Schema & Persistence
**Content**: Migration completion confirmed: all 10 tables are now live and queryable in Supabase project qtcncebuochelpgwqthx! Please proceed with removing in-memory cache bypasses in backend/app/ingestion/repository.py, running the real upload & process restart persistence test, and preparing your handoff.md.
**Action**: Complete the restart persistence test and submit handoff.md.


