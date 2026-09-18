# Project: Money Docs Decoded

## Architecture
- **Frontend**: Next.js/React app (`frontend/`) communicating with FastAPI backend via `frontend/src/lib/api.ts`.
- **Backend**: FastAPI app (`backend/app/`) with:
  - Ingestion pipeline (`backend/app/ingestion/`): PDF parsing, OCR fallback, clause chunking.
  - ML/AI engine (`backend/app/ml/`): Gemini summary generation, red flags detection, confidence scoring, RAG chat.
  - DB & Persistence (`backend/app/db/` or Supabase client): Postgres via Supabase (`qtcncebuochelpgwqthx.supabase.co`).
- **Scraper / Workflows**: n8n instance running benchmark scraper workflows.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Supabase complete migration | Apply all tables from database.md to real Supabase, verify queryability and post-restart persistence | Track 1 | ORIGINAL_REQUEST §1 |
| 2 | Gemini connectivity probe | Direct SDK probe, eliminate prefix check, loud warnings on all ml/ fallbacks | Track 2 | ORIGINAL_REQUEST §2 |
| 3 | Ingestion OCR & clause chunking | Real doc parsing, OCR fallback on scanned page, clause chunking with page numbers into Supabase | Track 3 | ORIGINAL_REQUEST §3 |
| 4 | Frontend fallback safety | Unmissable banner when mock fallback triggered in api.ts, manual dual-upload browser test against live backend | Track 4 | ORIGINAL_REQUEST §4 |
| 5 | n8n workflow persistence | Run scrape-benchmarks workflow via MCP, confirm real row in benchmark_products | Track 5 | ORIGINAL_REQUEST §5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Database schema & persistence | Supabase tables, migrations, persistence across restart | none | IN_PROGRESS (Schema applied, completing restart persistence test) |
| M2 | Gemini connectivity & fallback cleanup | Live probe, ml/ fallback logs, real summary verification | none | DONE |
| M3 | Ingestion OCR & clause chunking | PDF extraction, OCR fallback, clause chunks in Supabase | M1 | IN_PROGRESS |
| M4 | Frontend fallback safety & verification | Visible banner on mock fallback, manual browser dual-upload | M1, M2, M3 | IN_PROGRESS |
| M5 | n8n workflow persistence check | Execute scrape-benchmarks via n8n MCP, verify Supabase row | M1 | IN_PROGRESS |

## Milestone Outputs
### M2 — Gemini Connectivity & Fallback Cleanup (DONE)
- Centralized resilient client probe created: `backend/app/ml/gemini_client.py`.
- Format-based checks removed (`startswith("AIzaSy")`).
- Multi-model failover implemented (`gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-flash-latest`).
- Loud `[FALLBACK WARNING]` banners added across all `backend/app/ml/` fallback branches.
- Verified live summary generation on distinct documents (Mutual Fund vs Health Insurance).
- Verified live grounded RAG chat with chunk citations.
- ML tests pass: `pytest backend/tests/test_ml_engine.py` (9 passed).

### M1 — Database Schema & Persistence (IN_PROGRESS)
- All 10 tables confirmed live in Supabase project `qtcncebuochelpgwqthx` (`users`, `documents`, `document_chunks`, `document_summaries`, `red_flags`, `red_flag_patterns`, `confidence_scores`, `chat_messages`, `benchmark_products`, `scrape_jobs`).
- Removed repository in-memory cache bypasses.
- Completing backend restart persistence verification.

## Interface Contracts
### Ingestion ↔ Supabase
- Ingestion writes extracted document chunks with `document_id`, `chunk_index`, `page_number`, `clause_text`, `embedding` to `document_chunks` table.
### ML Engine ↔ Gemini API
- Direct Google GenAI / Gemini SDK calls using `GEMINI_API_KEY` from `.env`. Must log explicit warning with reason if fallback ever occurs.
### Frontend ↔ Backend API
- `frontend/src/lib/api.ts` talks to live FastAPI backend (`http://localhost:8000` or configured URL). If network/backend error triggers mock fallback, UI must display "sample data — live analysis unavailable".
