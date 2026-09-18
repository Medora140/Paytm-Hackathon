# DISPATCH — Track 3: Ingestion Pipeline (OCR & Chunking)

## Task Objective
You are Worker 3 (Ingestion Pipeline Specialist) for "Money Docs Decoded".
Your assigned working directory is:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track3_ingestion

You MUST read the authoritative request file before starting:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\ORIGINAL_REQUEST.md
Also read:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\backEnd.md
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\architecture.md

## Scope & File Ownership
You exclusively own:
- backend/app/ingestion/ directory (pdf_extractor.py, ocr_processor.py, clause_chunker.py, etc.)
- Ingestion verification scripts and tests

## Detailed Requirements
1. Re-verify end-to-end against a fresh upload of a real PDF:
   - Use the mutual fund handbook in `backend/tests/` (e.g. sample mutual fund scheme document or handbook).
   - Plus at least one other real document type (e.g. health insurance policy or loan agreement).
2. Test the text extraction, OCR fallback path (test with an actual scanned/image-based page, not just a text-native PDF), and clause-level chunking with page numbers.
3. Confirm chunks are actually written to and readable from the real Supabase `document_chunks` table (all Supabase tables are now live in project qtcncebuochelpgwqthx).
4. Remove any fallback to synthetic or mock chunks.
5. Criterion:
   - Two different real documents produce two different, correctly page-tagged chunk sets, verified by direct database query.
   - Chunks are stored in real Supabase `document_chunks` table.
   - Document the exact query commands and outputs proving genuine chunk sets.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. An auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Reporting
- Keep progress.md updated in your working directory.
- When finished, write a complete handoff.md in your working directory.
- Send a completion message via send_message to orchestrator conversation ID: b60453ca-e885-497d-b03a-0a1263a67b95.

## 2026-09-18T11:55:48Z
You are Worker 3 (Ingestion Pipeline Specialist: OCR & Clause Chunking) for "Money Docs Decoded".
Your assigned working directory is:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track3_ingestion

Read your task dispatch file and the authoritative request file before starting:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track3_ingestion\DISPATCH.md
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\ORIGINAL_REQUEST.md
Also read:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\backEnd.md
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\architecture.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. An auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Boundaries:
You own: backend/app/ingestion/ (PDF extraction, OCR fallback, clause chunking) and ingestion verification against Supabase.

Tasks:
1. Re-verify end-to-end against a fresh upload of a real PDF:
   - The mutual fund handbook in backend/tests/ (or sample mutual fund document).
   - At least one other real document type (e.g. health insurance policy or loan agreement).
2. Test text extraction, OCR fallback path (with an actual scanned/image-based page, not just a text-native PDF), and clause-level chunking with page numbers.
3. Confirm chunks are actually written to and readable from the real Supabase `document_chunks` table (all tables in Supabase project qtcncebuochelpgwqthx are now live!).
4. Criterion:
   - Two different real documents produce two different, correctly page-tagged chunk sets, verified by direct database query.
   - Zero fallback to synthetic or mock chunks.
   - Provide exact query outputs proving chunks in Supabase.

Regularly update progress.md in your working directory.
When complete, write a comprehensive handoff.md in your working directory and notify the orchestrator via send_message to conversation ID b60453ca-e885-497d-b03a-0a1263a67b95.

