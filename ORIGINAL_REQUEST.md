# Original User Request

## 2026-09-18T10:39:37Z

PROJECT: Money Docs Decoded — an AI-powered financial document analysis tool (health insurance/loan/mutual fund documents). Full specs live in these files, which every agent must read before touching related code:
- docs/architecture.md (system architecture, build order)
- docs/frontEnd.md (pages, states, what's real vs. fallback)
- docs/backEnd.md (API contract, services)
- docs/aiEngine.md (summary generation, red-flag detection, confidence score, RAG chat)
- docs/webScrap.md (benchmark scraper)
- docs/database.md (exact table definitions — the source of truth for what must exist in Supabase)
- docs/n8n.md
- docs/infra-deploy-security.md

Working directory: c:\Users\Medora Gomes\Desktop\money-docs-decoded
Integrity mode: development

CURRENT STATE — READ THIS BEFORE STARTING, DO NOT RE-DIAGNOSE FROM SCRATCH:
The project has been built by prior agent runs but is currently broken in ways that were partially diagnosed already:
1. Supabase tables from database.md were never actually applied to the real project (host: qtcncebuochelpgwqthx.supabase.co). document_chunks specifically was confirmed missing (error PGRST205: "Could not find the table 'public.document_chunks' in the schema cache"). A prior fix worked around this by reading from an in-memory repository cache instead of fixing the schema — meaning nothing is actually persisted, and everything will break again on any backend restart.
2. Gemini API calls were previously being silently skipped due to a bad key-format check (rejecting a valid AQ.-prefixed key), with the code falling back to static canned templates instead of calling Gemini. A fix was applied for this but the user is again seeing no Gemini calls happening and mock data being served — treat this as regressed or incompletely fixed, do not assume it's resolved.
3. OCR and clause chunking (backend/app/ingestion/) have not been re-verified against a real, fresh upload since these fixes — assume they may also be silently falling back or failing until proven otherwise.
4. The frontend has a mock-data fallback (src/lib/mockData.ts, used by src/lib/api.ts) that can silently render fake data with no visual indication it's fake — this is how a loan-summary + health-insurance-red-flags mismatch previously reached the screen undetected.

The recurring failure pattern across every previous fix in this project: agents patch a symptom (e.g., read from a cache instead of the database) rather than the root cause (e.g., the database table doesn't exist), and then report tests as "passing" because the patched path works — even though the underlying integration is still broken. Every agent below must treat this pattern as the primary risk and verify against REAL infrastructure, not workarounds.

SPAWN PARALLEL AGENTS ON THESE TRACKS:

AGENT 1 — Database schema & persistence (owns: Supabase project state, migrations/)
- Apply the COMPLETE migration from database.md against the real Supabase project — every table (documents, document_chunks, red_flags, red_flag_patterns, confidence_scores, chat_messages, benchmark_products, scrape_jobs), not just document_chunks.
- Confirm via a direct query (not through the app) that every table exists and is queryable.
- Do not mark this done until: a document uploaded through the real API has its chunks visible via a direct Supabase query, AND remains visible after a full backend process restart (kill and restart the server, then query again without re-uploading).

AGENT 2 — Gemini connectivity (owns: backend/app/ml/summary_generator.py, rag_chat.py)
- Verify the actual GEMINI_API_KEY currently in .env, and confirm it produces a real response with a direct, minimal test call to the Gemini SDK, isolated from the rest of the app.
- Find and remove ANY remaining format-based key validation (prefix checks like startswith("AIzaSy")) — replace with a live connectivity probe, cached, that only falls back on an actual failed call, with the real error logged.
- Grep the entire ml/ directory for every fallback branch and make each one log a loud, visible warning (not a silent return) including the specific reason it fired.
- Do not mark this done until: uploading a real document and requesting its summary produces a response that changes when the input document changes, with a log line confirming a live Gemini call was made (not a fallback).

AGENT 3 — Ingestion pipeline: OCR & chunking (owns: backend/app/ingestion/)
- Re-verify end-to-end against a fresh upload of a real PDF (the mutual fund handbook in backend/tests/, plus at least one other real document type): text extraction, OCR fallback path (test with an actual scanned/image-based page, not just a text-native PDF), clause-level chunking with page numbers.
- Confirm chunks are actually written to and readable from the real Supabase document_chunks table (depends on Agent 1's fix — coordinate or wait if needed).
- Do not mark this done until: two different real documents produce two different, correctly page-tagged chunk sets, verified by direct database query, with no fallback to synthetic/mock chunks.

AGENT 4 — Frontend fallback safety (owns: frontend/src/lib/api.ts, mockData.ts, and dashboard pages)
- Make the mock-data fallback path in api.ts impossible to trigger silently: if it ever fires, the UI must show a visible "sample data — live analysis unavailable" banner, never present fake data as if it were real.
- Manually test in a real browser: upload two different real documents in two separate sessions, confirm the dashboard shows genuinely different summaries, red flags, and confidence scores for each, with no mixed categories (e.g. never a loan-only phrase alongside health-insurance-only red flags).
- Do not mark this done until this manual dual-upload test is confirmed against the live backend from Agents 1–3, not against mocks.

AGENT 5 — n8n workflow persistence check (owns: n8n instance workflows only, via MCP)
- Re-run the scrape-benchmarks workflow and confirm the resulting benchmark_products row actually exists in the real Supabase table afterward via direct query — not just that the webhook returned success:true.
- Do not mark this done until a real row is confirmed post-scrape.

CROSS-CUTTING RULES FOR ALL AGENTS:
- "Tests passed" is not sufficient evidence of a fix. Every agent must report the actual real-world verification output specified in its "do not mark done until" criterion — direct query results, real Gemini response content, or a described manual browser test — not just a test-runner summary.
- If any agent finds it is blocked by another agent's unfinished work, state that explicitly rather than building a workaround/fallback to route around it — workarounds-in-place-of-fixes are the exact pattern that caused the current state.
- Report back per-agent with: what was actually broken, what was changed, and the specific verification evidence requested above.

## 2026-09-18T11:55:14Z

MIGRATION COMPLETE CONFIRMED! Direct query confirms all 10 tables are present in Supabase schema cache: ['users', 'red_flag_patterns', 'red_flags', 'document_summaries', 'confidence_scores', 'documents', 'scrape_jobs', 'document_chunks', 'benchmark_products', 'chat_messages'].
Informed Worker Gen 2 and Orchestrator to proceed with physical persistence verification and dispatch of Tracks 3, 4, 5.

