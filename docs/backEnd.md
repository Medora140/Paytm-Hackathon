# Backend — Component Spec

**Role:** The backend is the orchestrator. It owns every workflow that turns a raw PDF into a plain-language, cited, scored, benchmarked answer — and it is the only component allowed to talk to storage, the LLM, and the scraper. Frontend and n8n both go through it; they never talk to the database or LLM directly.

**Recommended stack:** FastAPI (Python) — pairs naturally with the ML/OCR stack (pypdf, unstructured, sentence-transformers) and the Gemini Python SDK (`google-generativeai` / `google-genai`). Async endpoints with background task queue (Celery + Redis, or simple FastAPI `BackgroundTasks` for hackathon scope) for anything slower than ~2 seconds (OCR, embedding, LLM summarization).

**Note on the free Gemini API key:** the free tier has real rate limits (requests/minute and requests/day) that are easy to hit during a live demo or a burst of test uploads. Build the request queue/backoff/caching mentioned under "Cost/rate control" below from day one rather than adding it later.
## Core services

### 1. Auth service
- Session/JWT validation (delegate actual auth to Supabase Auth or Clerk rather than rolling your own).
- Per-user document ownership checks on every document-scoped endpoint.

### 2. Ingestion service
**Owns:** turning an uploaded file into structured, searchable text.
**Workflow:**
1. Receive file → store raw file in object storage (S3-compatible bucket) → create `document` DB row with status `uploaded`.
2. Detect file type: text-native PDF vs. scanned/image PDF.
3. Text-native → direct text extraction (pypdf/pdfplumber). Scanned → OCR (Tesseract or a hosted OCR API) → status `extracted`.
4. Clause-level chunking: split extracted text into semantically coherent chunks (by clause/section headers, not fixed character count) and tag each chunk with page number → status `chunked`.
5. Embed each chunk (embedding model) and store in the vector table alongside the document ID and page number → status `embedded`.
6. Trigger the ML analysis service (below) → status `analyzed` when summary + red flags + confidence score are ready.

Expose the pipeline stage on the `GET /documents/{id}/status` endpoint so the frontend's multi-stage progress bar has something real to show.

### 3. ML analysis service (calls into `03-ml-ai-engine.md`)
**Owns:** the three AI-facing features.
- `POST /documents/{id}/summary` → plain-language summary (idempotent, cached after first run).
- `POST /documents/{id}/red-flags` → runs the red-flag detector against the document's chunks + KB.
- `POST /documents/{id}/confidence-score` → computes the aggregate score from red flags + benchmark deltas.
- `POST /documents/{id}/chat` → RAG query: embed user question, retrieve top-k chunks, call LLM with retrieved chunks + citation instruction, return answer + source chunk references.

### 4. Benchmark/scraping service (calls into `04-web-scraping-intelligence.md`)
- `GET /documents/{id}/compare` → returns this document's key attributes alongside cached scraped comparables for the same product category and (where detectable) issuer.
- Internally, this endpoint reads from a `benchmark_products` table that is populated by scheduled scraping jobs (owned by n8n), not scraped live on request — live scraping on every user request is both slow and likely to get your IP blocked.

### 5. Red-flag knowledge base service
- CRUD over the rule/pattern library described in `03-ml-ai-engine.md`.
- `POST /kb/red-flags` (internal/admin only) to add new patterns as your ombudsman dataset grows.

### 6. Notification/job service
- Thin layer that receives webhooks from n8n (e.g., "scraping job finished," "re-analysis needed") and updates the relevant DB rows / pushes a websocket or polling-visible status update to the frontend.

## API surface (representative, not exhaustive)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/session` | Validate/refresh session |
| POST | `/documents` | Upload a new document (multipart) |
| GET | `/documents` | List current user's documents |
| GET | `/documents/{id}` | Get document metadata + status |
| DELETE | `/documents/{id}` | Delete document + associated data (DPDP compliance) |
| GET | `/documents/{id}/summary` | Plain-language summary |
| GET | `/documents/{id}/red-flags` | Red-flag list with citations |
| GET | `/documents/{id}/confidence-score` | Score + breakdown |
| POST | `/documents/{id}/chat` | Ask a question, get cited answer |
| GET | `/documents/{id}/compare` | Benchmark comparison table |
| POST | `/webhooks/n8n/scrape-complete` | n8n → backend callback |
| POST | `/webhooks/n8n/kb-updated` | n8n → backend callback |

## Cross-cutting backend concerns

- **Idempotency:** re-uploading the same document (hash match) should reuse existing analysis rather than reprocessing — saves LLM cost and demo time.
- **Cost/rate control:** cache LLM responses per document+question-hash; set hard per-user daily limits on chat calls (ties into freemium tiering from the pitch deck).
- **PII handling:** documents may contain names, policy numbers, health info. Strip/redact obvious PII (name, policy number, DOB) before sending chunks to any third-party LLM API where feasible, or clearly document that redaction is a stretch goal if not implemented in time.
- **Audit trail:** log every red-flag/confidence-score computation with the KB version and model version used, so a score can be explained/reproduced later (important if this becomes a real product with regulatory exposure).
- **Timeouts & fallbacks:** every LLM call needs a timeout and a graceful fallback (return partial summary rather than nothing).

## What the backend explicitly does NOT do

- No rendering/UI logic.
- No long-running scrape jobs synchronously inside a request — always hand off to n8n or a background worker and return immediately with a job/status handle.