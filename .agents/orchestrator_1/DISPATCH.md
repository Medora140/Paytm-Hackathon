# Dispatch Log

## 2026-09-18T10:41:20Z

You are the Project Orchestrator for "Money Docs Decoded".
Your assigned working directory is:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\orchestrator_1

Authoritative request file:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\ORIGINAL_REQUEST.md

Project root directory:
c:\Users\Medora Gomes\Desktop\money-docs-decoded

Initialize your BRIEFING.md and progress.md immediately in your working directory.
Your mission is to orchestrate and execute the complete resolution of the issues outlined in ORIGINAL_REQUEST.md across 5 tracks:

1. AGENT 1 — Database schema & persistence (owns: Supabase project state, migrations/):
   - Apply the COMPLETE migration from database.md against the real Supabase project — every table (documents, document_chunks, red_flags, red_flag_patterns, confidence_scores, chat_messages, benchmark_products, scrape_jobs), not just document_chunks.
   - Confirm via direct query (not through app) that every table exists and is queryable.
   - Criterion: a document uploaded through real API has its chunks visible via direct Supabase query, AND remains visible after full backend process restart (kill & restart server, then query again without re-uploading).

2. AGENT 2 — Gemini connectivity (owns: backend/app/ml/summary_generator.py, rag_chat.py):
   - Verify actual GEMINI_API_KEY in .env, confirm real response with direct minimal test call to Gemini SDK isolated from rest of app.
   - Find and remove ANY remaining format-based key validation (prefix checks like startswith("AIzaSy")) — replace with a live connectivity probe, cached, that only falls back on actual failed call, with real error logged.
   - Grep entire ml/ directory for every fallback branch and make each log a loud, visible warning with specific reason.
   - Criterion: uploading real document and requesting summary produces a response changing when input changes, with log line confirming live Gemini call was made (not fallback).

3. AGENT 3 — Ingestion pipeline: OCR & chunking (owns: backend/app/ingestion/):
   - Re-verify end-to-end against fresh upload of real PDF (mutual fund handbook in backend/tests/ plus at least one other real doc type): text extraction, OCR fallback path (actual scanned/image-based page), clause-level chunking with page numbers.
   - Confirm chunks actually written to and readable from real Supabase document_chunks table (coordinate with Agent 1).
   - Criterion: two different real docs produce two different, correctly page-tagged chunk sets, verified by direct DB query, with no fallback to synthetic/mock chunks.

4. AGENT 4 — Frontend fallback safety (owns: frontend/src/lib/api.ts, mockData.ts, and dashboard pages):
   - Make mock-data fallback in api.ts impossible to trigger silently: if it fires, UI must show visible "sample data — live analysis unavailable" banner.
   - Manually test in real browser: upload two different real documents in two separate sessions, confirm dashboard shows genuinely different summaries, red flags, and confidence scores for each, with no mixed categories.
   - Criterion: manual dual-upload test confirmed against live backend from Agents 1-3, not mocks.

5. AGENT 5 — n8n workflow persistence check (owns: n8n instance workflows only, via MCP):
   - Re-run scrape-benchmarks workflow and confirm resulting benchmark_products row exists in real Supabase table via direct query.
   - Criterion: real row confirmed post-scrape.

CROSS-CUTTING RULES:
- "Tests passed" is not sufficient. Every track must report actual real-world verification output.
- No workarounds or mocks in place of real fixes.
- Report back per-agent: what was broken, what changed, specific verification evidence.

Decompose and spawn specialist subagents under .agents/ for each track. Keep progress.md updated regularly so Sentinel liveness and progress monitoring can track your state. Report to Sentinel when all tracks are fully verified and complete.
