# DISPATCH — Track 2: Gemini Connectivity & Fallback Cleanup

## Task Objective
You are Worker 2 (Track 2) for "Money Docs Decoded".
Your assigned working directory is:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track2_gemini

You MUST read the authoritative request file before starting:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\ORIGINAL_REQUEST.md
Also read:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\aiEngine.md
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\backEnd.md

## Scope & File Ownership
You exclusively own:
- backend/app/ml/summary_generator.py
- backend/app/ml/rag_chat.py
- and related ML files in backend/app/ml/

## Detailed Requirements
1. Verify the actual GEMINI_API_KEY currently in .env, and confirm it produces a real response with a direct, minimal test call to the Gemini SDK, isolated from the rest of the app.
2. Find and remove ANY remaining format-based key validation (prefix checks like startswith("AIzaSy")) — replace with a live connectivity probe, cached, that only falls back on an actual failed call, with the real error logged.
3. Grep the entire ml/ directory for every fallback branch and make each one log a loud, visible warning (not a silent return) including the specific reason it fired.
4. Criterion:
   - Uploading a real document and requesting its summary produces a response that changes when the input document changes.
   - A log line confirms a live Gemini call was made (not a fallback).
   - Document the exact probe call, response, log lines, and evidence proving live Gemini execution.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. An auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Reporting
- Keep progress.md updated in your working directory.
- When finished, write a complete handoff.md in your working directory.
- Send a completion message via send_message to orchestrator conversation ID: b60453ca-e885-497d-b03a-0a1263a67b95.

## 2026-09-18T10:44:00Z
You are Worker 2 (Gemini Connectivity Specialist) for "Money Docs Decoded".
Your assigned working directory is:
c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track2_gemini

Read your task dispatch file and the authoritative request file before starting:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track2_gemini\DISPATCH.md
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\ORIGINAL_REQUEST.md
Also read:
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\aiEngine.md
- c:\Users\Medora Gomes\Desktop\money-docs-decoded\docs\backEnd.md

Scope & Boundaries:
You own: backend/app/ml/summary_generator.py, backend/app/ml/rag_chat.py, and all fallback logic in backend/app/ml/.

Tasks:
1. Verify the actual GEMINI_API_KEY currently in .env, and confirm it produces a real response with a direct, minimal test call to the Gemini SDK (google-generativeai / google-genai), isolated from the rest of the app.
2. Find and remove ANY remaining format-based key validation (prefix checks like startswith("AIzaSy")) — replace with a live connectivity probe, cached, that only falls back on an actual failed call, with the real error logged.
3. Grep the entire backend/app/ml/ directory for every fallback branch and make each one log a loud, visible warning (not a silent return) including the specific reason it fired.
4. Criterion:
   - Uploading a real document and requesting its summary produces a response that changes when the input document changes.
   - A log line confirms a live Gemini call was made (not a fallback).
   - Document the exact probe call, response, log lines, and evidence proving live Gemini execution.

## 2026-09-18T11:00:24Z
**Context**: Track 2 (Gemini Connectivity) Progress Check
**Content**: Checking in on Task 1 (isolated minimal test call to Gemini SDK) and Task 2/3 progress.
**Action**: Please update your progress.md with your latest status and findings.

