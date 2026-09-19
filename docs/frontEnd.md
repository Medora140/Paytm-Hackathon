# Frontend — Component Spec

**Role:** The frontend is the trust interface. Its only job is to make a dense, scary document feel simple, safe, and answerable in under 60 seconds. It does not do any document reasoning itself — it only uploads, displays, and lets the user converse. Visual identity/colors are already defined in your `design.md` — this file only covers structure, page-by-page content, and states, not styling.

**Recommended stack:** Next.js (App Router) + TypeScript + Tailwind, deployed on Render. React Query (or SWR) for data fetching, Zustand for lightweight client state (chat history, upload progress).

## Global elements (present on every page)

- **Persistent disclaimer footer/banner:** "Not financial or legal advice — always confirm with the issuer." Required for compliance and judge optics.
- **Language toggle:** English / Hindi, affects all AI-generated text, not the raw document.
- **Document switcher:** if a user has uploaded more than one document, a dropdown to switch context.
- **Global loading/skeleton states:** every AI-backed screen must show a skeleton, not a blank page, while waiting on the backend (OCR + LLM calls take several seconds).
- **Error boundary:** if the backend fails (bad OCR, LLM timeout, unsupported doc), show a specific, non-technical error with a retry button — never a raw stack trace.

## Pages

### 1. Landing / Marketing page (`/`)
**Purpose:** Explain the value prop in <10 seconds, get the user to upload.
**Contains:**
- Hero: "Understand your policy before you sign — or claim." + single CTA button ("Upload a document").
- 3-card feature strip (Plain-Language Breakdown / Red-Flag Detector / Ask Anything) — reuse copy from pitch deck.
- Trust strip: "Grounded in real IRDAI/RBI ombudsman data" + "Works on any PDF, any insurer."
- Sample document button — lets a judge/user try the flow with a pre-loaded demo PDF without uploading their own (critical for a smooth live demo).

### 2. Upload page (`/upload`)
**Purpose:** Get a document into the system with minimum friction.
**Contains:**
- Drag-and-drop + file picker (PDF only at launch; accept images for OCR fallback).
- Document type selector: Health Insurance / Loan Agreement / Mutual Fund (disable the ones not yet supported in v1, don't hide them — shows roadmap to judges).
- Optional: "Import from DigiLocker" button (stretch goal, can be a disabled/"coming soon" state for the demo).
- Upload progress bar with real stages surfaced to the user: "Uploading → Extracting text → Analyzing clauses → Ready" (this maps directly to backend pipeline stages and makes wait time feel purposeful).
- Privacy note inline: what happens to the file, how long it's stored, that it's not shared with the insurer.

### 3. Document Dashboard / Summary page (`/doc/[id]`)
**Purpose:** The core "wow" screen — plain-language summary + confidence score at a glance.
**Contains:**
- **Confidence Score widget:** large number (e.g., 68/100), color-coded, one-line interpretation ("Below-average fairness — 3 red flags found"). Must show *why* the score is what it is (link to red flags), never a bare number.
- **Plain-language summary card:** 3–6 bullet points auto-generated (coverage, exclusions, key fees, waiting periods) — this is the "Instant Summary" from the demo slide.
- **Red-Flag panel:** list of flagged clauses, each with: plain-language explanation, severity (High/Medium/Low), the exact source text with page number, and a "why this matters" tooltip citing the ombudsman-pattern basis.
- **Benchmark strip** (feeds from the web-scraping component): "This policy's room-rent cap is stricter than 6 of 8 comparable plans" — with a link to `/doc/[id]/compare`.
- CTA into the chat: "Ask a question about this document."

### 4. Conversational Q&A page (`/doc/[id]/chat`)
**Purpose:** Let the user ask free-form questions and get cited answers.
**Contains:**
- Standard chat UI (message list + input box), scoped to the single active document.
- Every AI answer must render with an inline citation chip (e.g., "Page 14, Clause 4.2") that expands to show the exact source text on click/tap.
- Suggested-question chips above the input, generated from the document's own red flags (e.g., "Will pre-existing conditions be covered?") — lowers the blank-page problem.
- A visible fallback state: if the LLM can't find an answer in the document, it must say so explicitly rather than guessing — surface this as a distinct message style (e.g., amber, "Not found in this document — you may need to contact the issuer directly").

### 5. Compare / Benchmark page (`/doc/[id]/compare`)
**Purpose:** Show how this document stacks up against similar products in the market (powered by the web-scraping component).
**Contains:**
- Comparison table: this document vs. 2–4 scraped comparable products, aligned by attribute (premium, room-rent cap, waiting period, exclusions, claim settlement ratio if available).
- Data-freshness label per scraped source ("Benchmark data last refreshed: 2 days ago") and a link to the source page — transparency about where benchmark numbers came from.
- Clear visual distinction between "from your document" (grounded, cited) vs. "from the web" (scraped, may be outdated) — do not let these two trust levels blur together.

### 6. History / My Documents page (`/documents`)
**Purpose:** Return users manage previously uploaded documents.
**Contains:**
- List of uploaded docs with type, upload date, confidence score, and quick delete/re-analyze actions.
- "Re-scan" action — re-runs analysis if the red-flag knowledge base or scraped benchmarks have been updated since upload (ties into the roadmap's "proactive alerts" feature).

### 7. Account / Settings page (`/settings`)
**Purpose:** Minimal account management.
**Contains:**
- Language preference, data retention/delete-my-data control (important for DPDP Act compliance), plan tier (Free/Paid) if the freemium model is implemented.

### 8. Admin/Internal dashboard (optional, judge-facing or internal only) (`/admin`)
**Purpose:** Not user-facing — lets your team monitor pipeline health during the live demo and afterward.
**Contains:**
- Recent uploads, pipeline stage failures, scraper job status (from n8n), red-flag KB size/last-updated timestamp.

## States every AI-driven page must design for

1. **Loading** (multi-stage, not a spinner — show pipeline stage).
2. **Empty** (no documents yet — push to `/upload`).
3. **Partial success** (e.g., OCR worked but red-flag detection found nothing — say "No red flags detected" positively, don't leave a blank panel).
4. **Low-confidence extraction** (scanned/handwritten doc, OCR quality poor) — flag this to the user rather than presenting garbled text as fact.
5. **Error** (upload failed, unsupported file, LLM/API timeout) — specific, actionable message.

## What the frontend explicitly does NOT do

- No PDF parsing, OCR, chunking, or LLM calls client-side — everything goes through the backend API.
- No storage of raw document text in client state beyond what's needed to render the current view (avoid leaking sensitive financial data into browser storage/caches beyond session needs).