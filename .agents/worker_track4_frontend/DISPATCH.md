# DISPATCH — Track 4: Frontend Fallback Safety & Browser Verification

## 2026-09-18T11:55:48Z

## Task Objective
You are Worker 4 (Frontend Fallback Safety Specialist) for "Money Docs Decoded".
Your assigned working directory is:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track4_frontend

You MUST read the authoritative request file before starting:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\ORIGINAL_REQUEST.md
Also read:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\frontEnd.md
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\backEnd.md

## Scope & File Ownership
You exclusively own:
- frontend/src/lib/api.ts
- frontend/src/lib/mockData.ts
- frontend dashboard pages and fallback banner components

## Detailed Requirements
1. Make the mock-data fallback path in `api.ts` impossible to trigger silently:
   - If the fallback ever fires (e.g. when network or backend fails), the UI must show a prominent, visible banner:
     "sample data — live analysis unavailable"
   - Never present fake data as if it were real.
2. Ensure the live backend API calls properly populate the UI without falling back to mock data when backend is running.
3. Manually test in a real browser (or automated headless browser script verifying the rendered DOM):
   - Upload two different real documents in two separate sessions.
   - Confirm the dashboard shows genuinely different summaries, red flags, and confidence scores for each.
   - Confirm no mixed categories (e.g. never a loan-only phrase alongside health-insurance-only red flags).
4. Criterion:
   - Manual dual-upload test confirmed against the live backend (FastAPI + Supabase + Gemini), NOT against mocks.
   - Fallback warning banner verified to display whenever mock data is active.
   - Document exact test steps, screenshots/logs, and verification evidence.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. An auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Reporting
- Keep progress.md updated in your working directory.
- When finished, write a complete handoff.md in your working directory.
- Send a completion message via send_message to orchestrator conversation ID: b60453ca-e885-497d-b03a-0a1263a67b95.
