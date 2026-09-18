# BRIEFING — 2026-09-18T11:55:48Z

## Mission
Ensure mock-data fallback in frontend api.ts is impossible to trigger silently (display prominent "sample data — live analysis unavailable" banner), verify live backend API calls populate the UI properly, and perform browser verification of dual document uploads showing genuine differences and no mixed categories.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: c:\Users\Medora Gomes\Desktop\money-docs-decoded\.agents\worker_track4_frontend
- Original parent: b60453ca-e885-497d-b03a-0a1263a67b95
- Milestone: Track 4 - Frontend Fallback Safety & Browser Verification

## 🔒 Key Constraints
- Owns: frontend/src/lib/api.ts, frontend/src/lib/mockData.ts, and frontend dashboard pages / fallback indicators.
- NEVER present fake data as if it were real: if fallback fires, show a prominent, visible banner: "sample data — live analysis unavailable".
- Ensure live backend calls populate UI properly when backend is up.
- Manually test in a real browser (or automated headless browser script verifying DOM):
  - Upload two different real documents in two separate sessions.
  - Confirm dashboard shows genuinely different summaries, red flags, and confidence scores for each, with no mixed categories.
- Dual-upload test MUST be confirmed against live backend (FastAPI + Supabase + Gemini), NOT against mocks.
- Mandatory integrity mandate: No cheating, no hardcoded results, no dummy facades.

## Current Parent
- Conversation ID: b60453ca-e885-497d-b03a-0a1263a67b95
- Updated: 2026-09-18T11:55:48Z

## Task Summary
- **What to build**: Visible fallback banner in frontend UI whenever mock data is returned, update api.ts / mockData.ts to tag/track fallback usage, ensure live API integration works seamlessly, run headless/real browser dual-upload tests and verify DOM outputs.
- **Success criteria**:
  1. Visible warning banner displayed whenever mock data fallback activates.
  2. Live backend API calls correctly populate UI without fallback when backend is running.
  3. Real browser / DOM test with two different real documents confirming distinct summaries, red flags, confidence scores, and no category mixing.
- **Interface contracts**: docs/frontEnd.md, docs/backEnd.md
- **Code layout**: frontend/

## Key Decisions Made
- [TBD]

## Artifact Index
- DISPATCH.md — Assignment from orchestrator
- progress.md — Liveness heartbeat and progress log
- handoff.md — Final handoff report

## Change Tracker
- **Files modified**: None yet
- **Build status**: Not run yet
- **Pending issues**: None

## Quality Status
- **Build/test result**: Not run yet
- **Lint status**: Not run yet
- **Tests added/modified**: None yet

## Loaded Skills
- None
