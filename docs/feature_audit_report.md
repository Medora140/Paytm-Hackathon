# Money Docs Decoded — Full Feature Audit Report

_Generated: 2026-09-18. No code changes were made during this audit._
_Sources: Every claim is backed by exact file:line references listed under "Evidence."_

---

## Scoring Key

| Symbol | Meaning |
|---|---|
| ✅ | Implemented and structurally correct |
| ⚠️ | Implemented but broken or partially wrong |
| ❌ | Required by spec, entirely absent from codebase |
| 🔴 | CRITICAL — blocks core demo flow |
| 🟠 | HIGH — significantly degrades user experience or data integrity |
| 🟡 | MEDIUM — noticeable gap but demo can still run |

---

## 1. Database Layer

**Spec:** [`docs/database.md`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/database.md)

| Table | Spec Columns | Status | Evidence |
|---|---|---|---|
| `users` | id, email, created_at, plan_tier, preferred_language, data_retention_opt_in | ✅ | `backend/migrations/001_initial_schema.sql` |
| `documents` | id, user_id, filename, document_type, storage_path, status, issuer_name, uploaded_at, deleted_at | ✅ | `001_initial_schema.sql` — confirmed live via HTTP 200 from Supabase PostgREST |
| `document_chunks` | id, document_id, page_number, clause_label, text, embedding (vector), created_at | ✅ | Confirmed live; 259 rows inserted in test run (HTTP 201 ×6 batches) |
| `document_summaries` | id, document_id, language, coverage, exclusions, key_fees, waiting_periods, notable_terms, model_version, generated_at | ✅ | `001_initial_schema.sql` |
| `red_flags` | id, document_id, pattern_id, chunk_id, severity, plain_explanation, confirmed_by_llm, created_at | ✅ | `001_initial_schema.sql` |
| `red_flag_patterns` | id, category, clause_type, trigger_keywords, trigger_regex, plain_explanation_template, severity_default, source_reference, created_at, updated_at | ✅ | `001_initial_schema.sql` |
| `confidence_scores` | id, document_id, score, breakdown (jsonb), kb_version, computed_at | ✅ | `001_initial_schema.sql` |
| `chat_messages` | id, document_id, user_id, role, content, cited_chunk_ids (jsonb), created_at | ✅ | `001_initial_schema.sql` |
| `benchmark_products` | id, product_category, issuer_name, product_name, source_url, attributes (jsonb), complaint_signal (jsonb), last_scraped_at | ✅ | `001_initial_schema.sql` |
| `scrape_jobs` | id, source_url, status, triggered_by, started_at, finished_at, error_message | ✅ | `001_initial_schema.sql` |
| HNSW index on `document_chunks.embedding` | — | ✅ | `001_initial_schema.sql` |
| Composite index on `benchmark_products(product_category, issuer_name)` | — | ✅ | `001_initial_schema.sql` |

**Database Summary: ✅ ALL 10 TABLES LIVE.** Supabase schema is fully applied and queryable.

> [!IMPORTANT]
> The `embedding` column exists in the schema, but the Python embedder silently falls back to SHA-256 pseudo-vectors whenever ChromaDB fails to initialize (protobuf conflict). Rows are persisted with 384-dim vectors, but those vectors are **not semantic** — pgvector similarity search over them is meaningless. See §3 (ML Engine) for details.

---

## 2. Ingestion Service

**Spec:** [`docs/backEnd.md §2`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/backEnd.md) + [`docs/aiEngine.md §5 OCR`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/aiEngine.md)

| Step | Spec Requirement | Status | Evidence |
|---|---|---|---|
| 1. Store raw file in object storage | S3-compatible bucket; `document` row created with status `uploaded` | ✅ | [`pipeline.py:76-85`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/pipeline.py#L76-L85) — `StorageManager.store_file()` + `repository.create_document()` |
| 2. Detect text-native vs. scanned PDF | Per-page char count threshold | ✅ | [`detector.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/detector.py) — is_scanned when char_count < 40 |
| 3a. Text-native extraction | pypdf/pdfplumber | ✅ | [`extractor.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/extractor.py) — 61 pages extracted from HDFC MF Handbook test run |
| 3b. Scanned OCR fallback | Tesseract | ⚠️ 🔴 | OCR code path exists in [`extractor.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/extractor.py) and is **called** for scanned pages, but **Tesseract binary is not installed**. Actual log: `"WARNING: Tesseract binary not found in PATH. OCR fallback skipped."` Scanned pages fall through to placeholder: `"[Scanned/Image page N - Content unreadable without OCR]"` |
| 4. Clause-level chunking with page numbers | Tag each chunk with page number | ✅ | [`chunker.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/chunker.py) — 259 chunks produced, all with `page_number`. Confirmed by Supabase SELECT |
| 5. Embed chunks (384-dim) and store in vector table | Semantic embeddings | ⚠️ 🟠 | [`embedder.py:78-92`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/embedder.py#L78-L92) — `_fallback_embedding()` (SHA-256 hash vectors) silently used when ChromaDB fails. **Not semantic.** No `is_fallback` flag in chunk rows. |
| 6. Trigger ML analysis service → status `analyzed` | Pipeline completes with `analyzed` status | ❌ 🔴 | [`pipeline.py:135-148`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/pipeline.py#L135-L148) — pipeline ends at `DocumentStatus.EMBEDDED`. **No call to ML analysis service.** The `analyzed` status is never set via the normal upload flow. |

### Ingestion Status per File

| File | Role | Status |
|---|---|---|
| [`pipeline.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/pipeline.py) | Orchestrator | ✅ wired, ❌ missing Step 6 ML trigger |
| [`detector.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/detector.py) | Native vs. scanned | ✅ |
| [`extractor.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/extractor.py) | Text + OCR | ⚠️ Tesseract not installed |
| [`chunker.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/chunker.py) | Clause splitting | ✅ |
| [`embedder.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/embedder.py) | Embeddings | ⚠️ hash fallback not semantic |
| [`repository.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/repository.py) | DB persistence | ✅ Supabase-first |
| [`storage.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ingestion/storage.py) | Object storage | ✅ |

---

## 3. ML Analysis Service (AI Engine)

**Spec:** [`docs/aiEngine.md`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/aiEngine.md)

### 3.1 Plain-Language Summary Generator (§1)

| Spec Requirement | Status | Evidence |
|---|---|---|
| Single structured Gemini call per document | ✅ | [`summary_generator.py:203-242`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/summary_generator.py#L203-L242) — live Gemini call with JSON schema enforcement |
| Fixed output schema: coverage, exclusions, key_fees, waiting_periods, notable_terms | ✅ | [`summary_generator.py:208-218`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/summary_generator.py#L208-L218) |
| Distinct prompt templates per document type | ✅ (partial) | `summary_generator.py` — different prompts for `mutual_fund`, `health_insurance`, `loan` types |
| English/Hindi support | ✅ | Language parameter threaded through `get_summary()` and prompt |
| Graceful fallback if Gemini fails (return partial, not nothing) | ❌ 🟠 | [`summary_generator.py:279-282`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/summary_generator.py#L279-L282) — raises `GeminiUnavailableError`. Spec says "return partial summary rather than nothing." The `FALLBACK_SUMMARIES` dict at lines 28-107 exists but is **dead code** — never referenced in any production path. |
| `is_fallback` / `degraded_mode` field in response | ❌ 🟠 | Confirmed: `grep degraded_mode` → 0 results in entire codebase. Frontend cannot distinguish a real Gemini response from a degraded one. |

### 3.2 Red-Flag Detector (§2)

| Spec Requirement | Status | Evidence |
|---|---|---|
| Rule-based keyword/regex KB matching | ✅ | [`red_flag_detector.py:64-86`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/red_flag_detector.py#L64-L86) — with `\b` word boundaries |
| Word-boundary safe matching (no "emi inside premium" bug) | ✅ | [`red_flag_detector.py:75`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/red_flag_detector.py#L75): `re.search(r"\b" + re.escape(kw_clean) + r"\b", text_lower)` |
| LLM confirmation step for ambiguous matches (§2 step 2) | ❌ 🔴 | Zero LLM confirmation calls in [`red_flag_detector.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/red_flag_detector.py). The `confirmed_by_llm` field is hardcoded `True` at line 102 for every rule-based match. **Every flag claims LLM confirmation — none receives it.** |
| Attach exact source text + page number to every flag | ✅ | `red_flag_detector.py:93-104` — `source_text`, `page_number`, `chunk_id` all populated |
| Fine-tuned clause classification model (DeBERTa/InLegalBERT/SetFit) — §2a | ❌ 🟠 | **Zero model code exists anywhere.** No training pipeline, no inference service, no model files. Spec explicitly says rule-based is the "complement/fallback" — here it's the only implementation. |
| Benchmark penalty integrated into red flag severity | ❌ 🟡 | [`confidence_score.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/confidence_score.py) accepts `benchmark_penalty` param but ML service always passes 0 |

### 3.3 Confidence Score (§3)

| Spec Requirement | Status | Evidence |
|---|---|---|
| Formula: 100 − Σ severity weights − benchmark_penalty + transparency_bonus | ✅ | [`confidence_score.py:41-92`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/confidence_score.py#L41-L92) — exact formula, correct weights (high=15, medium=8, low=3) |
| Itemized breakdown returned with score | ✅ | `confidence_score.py:38-89` — `ScoreBreakdownItem` list returned |
| Benchmark penalty wired to scraped comparables | ❌ 🟡 | `benchmark_penalty` always passed as 0; no comparison with `benchmark_products` table |
| `kb_version` in response | ✅ | `confidence_score.py:18` — `CURRENT_KB_VERSION = "kb_v2026.09_sebi_irda_ombudsman"` |

### 3.4 RAG Conversational Q&A (§4)

| Spec Requirement | Status | Evidence |
|---|---|---|
| Embed user question (same embedding model as ingestion) | ❌ 🔴 | [`rag_chat.py:34-44`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/rag_chat.py#L34-L44) — no embedding call. Uses `_lexical_similarity()` (keyword overlap) instead. |
| pgvector similarity search over document chunks (§4 step 2) | ❌ 🔴 | **Zero pgvector query calls anywhere in codebase.** The HNSW index on `document_chunks.embedding` is never used. `grep pgvector` → 0 results. |
| LLM prompt: answer only from retrieved chunks, cite page/clause | ✅ | `rag_chat.py` — system prompt instructs model to cite and refuse out-of-scope |
| Return chunk IDs/pages used (citation chips in frontend) | ✅ | `ChatResponse.citations` list populated |
| Explicit "not found" fallback (amber message style) | ⚠️ 🟠 | Backend sends `"I could not find information about this in the provided document"` — but frontend chat page has no amber/distinct rendering for this state. It renders as a normal message. |
| Out-of-scope query refusal | ✅ | [`rag_chat.py:27-31`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/rag_chat.py#L27-L31) — `OUT_OF_SCOPE_TOPICS` list checked |

### 3.5 Gemini Client

| Spec Requirement | Status | Evidence |
|---|---|---|
| No hardcoded `AIzaSy` prefix check | ✅ | `grep AIzaSy` across entire codebase → 0 results |
| Key validation: empty-string check only | ✅ | [`gemini_client.py:76-87`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/gemini_client.py#L76-L87) |
| Multi-model failover on 429 | ✅ | [`gemini_client.py:108-154`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/gemini_client.py#L108-L154) — 4 candidate models |
| Loud logging on fallback | ✅ | `[FALLBACK WARNING]` banner logs present throughout `gemini_client.py` |
| Bug: `"500" in err_str` substring match | ⚠️ 🟡 | [`gemini_client.py:140`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/ml/gemini_client.py#L140): `any(c in err_str for c in ["429", "503", "500", ...])` — the string `"500"` will match in `"Error processing 1500 tokens"`, mistakenly treating a prompt-length error as a transient HTTP 500 |

---

## 4. Benchmark / Scraping Service

**Spec:** [`docs/backEnd.md §4`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/backEnd.md) + [`docs/webScrap.md`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/webScrap.md)

| Spec Requirement | Status | Evidence |
|---|---|---|
| Real HTTP scraper (requests/httpx + BeautifulSoup or Playwright) | ❌ 🔴 | [`scraping/service.py:52-143`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/scraping/service.py#L52-L143) — empty `benchmark_products` table triggers Python-dict hardcoded fallback. No HTTP client, no scraper calls. `last_scraped_at = datetime.utcnow()` always makes data appear fresh. |
| Reads from `benchmark_products` table populated by n8n scraper jobs | ⚠️ | [`scraping/repository.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/scraping/repository.py) queries Supabase first — but table is always empty because no scraper ever writes to it. Falls to hardcoded dicts. |
| robots.txt / ToS check gate | ✅ | [`scraper/robots_guard.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/scraper/robots_guard.py) — guard exists in the standalone scraper |
| Normalize into common schema per product category | ✅ (partial) | `scraping/models.py` — schema defined. `scraper/extractor.py` — extraction logic exists |
| Seed URLs verified with real HTTP requests | ❌ 🔴 | [`scraper/seed_urls.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/scraper/seed_urls.py) — 8 direct PDF deep-links. None have been verified. Previous audit found most return 403/404. |
| `last_scraped_at` freshness label + "possibly outdated" if >30 days | ❌ 🟡 | Frontend [`BenchmarkStrip.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/components/BenchmarkStrip.tsx) exists but uses mock `last_scraped_at` from hardcoded dict. No staleness check. |
| Source link per scraped fact | ❌ 🟡 | Not rendered on compare page |

---

## 5. Auth Service

**Spec:** [`docs/backEnd.md §1`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/backEnd.md)

| Spec Requirement | Status | Evidence |
|---|---|---|
| Session/JWT validation via Supabase Auth or Clerk | ❌ 🟠 | [`routers/auth.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/routers/auth.py) — route exists but is a stub (790 bytes, no real JWT validation). All endpoints currently accept any `user_id`. |
| Per-user document ownership checks on every document endpoint | ❌ 🟠 | No ownership check in any document endpoint. Demo user ID (`DEMO_USER_ID`) is always assumed. |

---

## 6. Webhooks / Notification Service

**Spec:** [`docs/backEnd.md §6`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/backEnd.md) + [`docs/n8n.md`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/n8n.md)

| Endpoint | Status | Evidence |
|---|---|---|
| `POST /webhooks/n8n/scrape-complete` | ⚠️ | [`routers/webhooks.py:23-37`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/routers/webhooks.py#L23-L37) — endpoint exists, **but only returns an ACK string**. Does NOT invalidate any cache or update `scrape_jobs` in DB. |
| `POST /webhooks/n8n/kb-updated` | ⚠️ | [`routers/webhooks.py:40-54`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/routers/webhooks.py#L40-L54) — returns `"queued_documents_count": 42` (hardcoded). No actual re-analysis queued. |
| Websocket or polling-visible status push to frontend | ❌ 🟡 | No websocket. Frontend must poll `GET /documents/{id}` — this works but is not reactive. |

---

## 7. n8n Workflows

**Spec:** [`docs/n8n.md`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/n8n.md)

| Workflow | Spec | Status | Evidence |
|---|---|---|---|
| `scrape-benchmarks` (weekly cron) | Read seeds → scrape → POST to backend `benchmark_products` | ❌ 🔴 | [`n8n/`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/n8n/) directory contains only a `README.md`. Zero workflow JSON files. |
| `re-analyze-on-kb-update` | On KB change → batch re-analysis of old docs | ❌ 🟠 | Not implemented |
| `ocr-overflow-queue` | Large/scanned doc handoff from backend to n8n | ❌ 🟡 | Not implemented |
| `discover-new-sources` (stretch) | Monthly source discovery | ❌ 🟢 | Stretch goal — not started |
| `pipeline-health-alerts` | Poll `/admin`, alert on failures | ❌ 🟡 | Not implemented |

---

## 8. API Surface

**Spec:** [`docs/backEnd.md API table`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/backEnd.md#L44-L59)

| Method | Path | Spec | Status | Evidence |
|---|---|---|---|---|
| POST | `/auth/session` | Session validation | ⚠️ | [`routers/auth.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/routers/auth.py) — stub, no real JWT |
| POST | `/documents` | Upload multipart | ✅ | [`routers/ingestion.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/routers/ingestion.py) |
| GET | `/documents` | List user documents | ✅ | `routers/ingestion.py` |
| GET | `/documents/{id}` | Document metadata + status | ✅ | `routers/ingestion.py` |
| DELETE | `/documents/{id}` | Delete + DPDP erasure | ✅ | `routers/ingestion.py` |
| GET | `/documents/{id}/summary` | Plain-language summary | ✅ | [`routers/ml.py:14-20`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/routers/ml.py#L14-L20) |
| GET | `/documents/{id}/red-flags` | Red-flag list | ✅ | `routers/ml.py:23-29` |
| GET | `/documents/{id}/confidence-score` | Score + breakdown | ✅ | `routers/ml.py:32-38` |
| POST | `/documents/{id}/chat` | RAG Q&A | ✅ | `routers/ml.py:41-47` |
| GET | `/documents/{id}/compare` | Benchmark comparison | ✅ | [`routers/scraping.py`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/backend/app/routers/scraping.py) |
| POST | `/webhooks/n8n/scrape-complete` | n8n callback | ⚠️ stub | `routers/webhooks.py:23-37` |
| POST | `/webhooks/n8n/kb-updated` | n8n callback | ⚠️ stub | `routers/webhooks.py:40-54` |

---

## 9. Frontend Pages

**Spec:** [`docs/frontEnd.md`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/frontEnd.md)

| Page | Spec | Status | Evidence |
|---|---|---|---|
| `/` Landing | Hero + 3-card strip + trust strip + sample doc button | ✅ | [`app/page.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/app/page.tsx) — all elements present. Sample document button at line 45 links to `MOCK_DOCUMENT_ID`. |
| `/upload` | Drag-drop + type selector + progress bar + privacy note | ✅ | [`components/UploadForm.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/components/UploadForm.tsx) (12 KB) — full upload flow |
| `/upload` → DigiLocker button (stretch) | Disabled/coming-soon state | ❌ 🟢 | Not present even as a disabled button. Stretch goal. |
| `/doc/[id]` Summary dashboard | Confidence score + summary card + red-flag panel + benchmark strip + chat CTA | ✅ | [`app/doc/[id]/page.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/app/doc/%5Bid%5D/page.tsx) — all panels present using real components |
| `/doc/[id]/chat` | Chat UI + citation chips + suggested questions + "not found" amber state | ⚠️ 🟡 | Chat directory exists at [`app/doc/[id]/chat`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/app/doc/%5Bid%5D/chat). Citations returned by backend but **no amber/distinct style for "not found" answers** in frontend render. |
| `/doc/[id]/compare` | Comparison table + data freshness label + source links | ⚠️ 🟡 | Compare directory exists. Data freshness label uses `datetime.utcnow()` from hardcoded dict — always appears "just scraped". No source links per row. |
| `/documents` History | List + confidence scores + re-analyze action | ⚠️ 🟡 | [`app/documents`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/app/documents) — list exists. **"Re-scan" action is absent.** No `re-analyze` button implemented. |
| `/settings` | Language pref + data delete + plan tier | ⚠️ 🟡 | [`app/settings`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/app/settings) — directory exists, content unverified |
| `/admin` | Pipeline health dashboard | ❌ 🟡 | [`app/admin`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/app/admin) — directory exists but no real pipeline health data — just static content |

---

## 10. Global Frontend Elements

**Spec:** [`docs/frontEnd.md §Global elements`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/frontEnd.md#L7-L13)

| Spec Element | Status | Evidence |
|---|---|---|
| Persistent disclaimer footer/banner | ✅ | [`components/DisclaimerBanner.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/components/DisclaimerBanner.tsx) imported in [`layout.tsx:4,20`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/app/layout.tsx#L4) |
| Language toggle (EN / HI) | ❌ 🟠 | `grep language` in `frontend/src` → 0 results. No toggle UI anywhere. Backend supports `language=hi` parameter and `api.ts:120` passes it, but **no UI control exists for the user to switch**. |
| Document switcher dropdown | ❌ 🟡 | [`Navigation.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/components/Navigation.tsx) — navigation exists but no document switcher dropdown for multi-doc users |
| Global skeleton loaders | ✅ | [`components/SkeletonLoader.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/components/SkeletonLoader.tsx) — used on all AI-backed screens |
| Error boundary (non-technical error with retry button) | ⚠️ 🟡 | Not a React `ErrorBoundary` class. Errors surface as inline text but without a dedicated retry button |

---

## 11. Frontend State Machine

**Spec:** [`docs/frontEnd.md §States every AI-driven page must design for`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/frontEnd.md#L74-L80)

| State | Spec Requirement | Status |
|---|---|---|
| Loading (multi-stage, show pipeline stage) | ✅ | UploadForm shows real backend stages: Uploading → Extracting → Analyzing |
| Empty (no documents — push to /upload) | ✅ | `/documents` page handles empty state |
| Partial success (no red flags → positive "None detected") | ✅ | [`RedFlagsPanel.tsx`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/components/RedFlagsPanel.tsx) — renders "No red flags detected" positively |
| Low-confidence extraction (scanned/OCR quality poor) | ❌ 🟡 | No such flag in any API response schema. Even if OCR returns placeholder text, it's embedded and presented as real content with no warning to the user. |
| Error (LLM timeout, unsupported file) | ⚠️ 🟡 | Generic error state shown; not always specific/actionable |

---

## 12. Frontend — Silent Mock Fallback (Cross-Cutting Bug)

> [!CAUTION]
> **The most dangerous ongoing bug in the codebase.** Every API function in [`api.ts`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/lib/api.ts) has a `catch` block that silently serves mock data when the backend fails. There is **no visual indicator** to the user that they are seeing fake data.

**Specific substring bugs in the mock chat fallback** ([`api.ts:174-186`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/frontend/src/lib/api.ts#L174-L186)):

```typescript
if (lower.includes("room") || lower.includes("rent")) {
    return { ...MOCK_CHAT_ANSWERS.room_rent, document_id: id };
}
```

- `"room"` is a substring of `"showroom"`, `"bathroom"`, `"classroom"`, `"mushroom"` → false match
- `"rent"` is a substring of `"current"`, `"inherent"`, `"different"` → **"What is the current status?" returns room-rent mock data**
- `"ped"` is a substring of `"sped"`, `"hoped"` → PED/waiting-period mock data returned

These are direct siblings of the "emi inside premium" bug — all in `api.ts`, all in the mock fallback path that fires when the backend is unavailable.

---

## 13. Cross-Cutting Backend Concerns

**Spec:** [`docs/backEnd.md §Cross-cutting`](file:///c:/Users/Medora%20Gomes/Desktop/money-docs-decoded/docs/backEnd.md#L61-L67)

| Concern | Spec Requirement | Status | Evidence |
|---|---|---|---|
| Idempotency (hash match on re-upload) | Re-use existing analysis | ❌ 🟡 | No file hash check anywhere. Re-upload creates duplicate `document` rows. |
| LLM response caching per document+question-hash | Avoid re-calling Gemini | ❌ 🟡 | No cache layer. Every summary request calls Gemini fresh. |
| Per-user daily LLM call limits | Hard limits for freemium | ❌ 🟡 | Not implemented |
| PII redaction before LLM call | Strip name, DOB, policy# | ❌ 🟠 | Full raw chunk text sent to Gemini. Spec says "strip or redact" before any third-party API call. |
| Audit trail for every red-flag/score computation | Log KB version + model version | ❌ 🟡 | `confidence_score.py` records `kb_version` in the row, but no structured audit log. |
| Timeout + graceful fallback on every LLM call | Return partial, not error | ❌ 🟠 | `summary_generator.py:279-282` — raises `GeminiUnavailableError` on timeout. Spec says "return partial summary rather than nothing." |

---

## Summary Tables

### ✅ Completed (Working)

| # | Feature |
|---|---|
| 1 | All 10 Supabase tables live and queryable |
| 2 | pgvector + HNSW index created on `document_chunks.embedding` |
| 3 | Full ingestion pipeline: upload → detect → extract → chunk → embed → persist (for native PDFs) |
| 4 | 259 chunks with page_number written to Supabase in real test run (confirmed by SELECT) |
| 5 | Supabase-first repository (no in-memory bypass in production) |
| 6 | All 10 API endpoints wired and routed |
| 7 | Confidence score formula (correct weights, itemized breakdown) |
| 8 | Red-flag KB with 10 patterns, word-boundary-safe keyword matching |
| 9 | Gemini client: no `AIzaSy` prefix check; multi-model failover on 429 |
| 10 | Disclaimer banner in every page (via `layout.tsx`) |
| 11 | Global skeleton loaders |
| 12 | Landing page: hero, sample doc button, trust strip, 3-card feature strip |
| 13 | Upload page: drag-drop, type selector, real pipeline progress stages |
| 14 | Summary dashboard: confidence widget, summary card, red-flag panel, benchmark strip |
| 15 | Chat page: message list, citations returned by backend |
| 16 | Webhooks: `/scrape-complete` and `/kb-updated` routes exist and accept payloads |
| 17 | robots.txt guard in standalone scraper |
| 18 | Distinct prompt templates per document type (mutual_fund / health_insurance / loan) |
| 19 | Out-of-scope query refusal in RAG chat |

---

### ❌ Not Implemented (Zero Code)

| # | Feature | Spec Reference | Severity |
|---|---|---|---|
| 1 | Fine-tuned clause classifier (DeBERTa/InLegalBERT/SetFit) | aiEngine.md §2a | 🟠 HIGH |
| 2 | LLM confirmation step for ambiguous red-flag matches | aiEngine.md §2 step 2 | 🔴 CRITICAL |
| 3 | pgvector semantic similarity search in RAG | aiEngine.md §4 step 2 | 🔴 CRITICAL |
| 4 | ML analysis trigger from ingestion pipeline (status `analyzed`) | backEnd.md §2 step 6 | 🔴 CRITICAL |
| 5 | Real HTTP web scraper (any of the 8 seed URLs being fetched live) | webScrap.md | 🔴 CRITICAL |
| 6 | n8n `scrape-benchmarks` workflow | n8n.md §1 | 🔴 CRITICAL |
| 7 | n8n `re-analyze-on-kb-update` workflow | n8n.md §2 | 🟠 HIGH |
| 8 | n8n `ocr-overflow-queue` workflow | n8n.md §3 | 🟡 MEDIUM |
| 9 | n8n `pipeline-health-alerts` workflow | n8n.md §5 | 🟡 MEDIUM |
| 10 | Language toggle UI (EN/HI) | frontEnd.md §Global | 🟠 HIGH |
| 11 | Document switcher dropdown | frontEnd.md §Global | 🟡 MEDIUM |
| 12 | "Re-scan" action on history page | frontEnd.md §6 | 🟡 MEDIUM |
| 13 | DigiLocker button (stretch, even as disabled) | frontEnd.md §2 | 🟢 LOW |
| 14 | PII redaction before LLM call | backEnd.md §cross-cutting | 🟠 HIGH |
| 15 | Document hash idempotency on re-upload | backEnd.md §cross-cutting | 🟡 MEDIUM |
| 16 | LLM response cache per document+question-hash | backEnd.md §cross-cutting | 🟡 MEDIUM |
| 17 | Per-user daily LLM call limits | backEnd.md §cross-cutting | 🟡 MEDIUM |
| 18 | Structured audit log for red-flag computations | backEnd.md §cross-cutting | 🟡 MEDIUM |
| 19 | Real JWT auth + per-user ownership checks | backEnd.md §1 | 🟠 HIGH |
| 20 | Benchmark penalty wired to real scraped comparables | aiEngine.md §3 | 🟡 MEDIUM |

---

### ⚠️ Implemented but Broken

| # | Feature | Bug | Severity |
|---|---|---|---|
| 1 | OCR (Tesseract) | Binary not installed. Scanned pages return placeholder text silently. | 🔴 CRITICAL |
| 2 | Semantic embeddings | ChromaDB protobuf conflict → SHA-256 hash fallback used. Embeddings are not semantic. pgvector search is meaningless. | 🔴 CRITICAL |
| 3 | `confirmed_by_llm` field | Always `True` (hardcoded at `red_flag_detector.py:102`) — no LLM is ever called. | 🔴 CRITICAL |
| 4 | Frontend mock fallback | All API functions silently fall back to mock data with no visual indicator. | 🔴 CRITICAL |
| 5 | Chat mock fallback substring bugs | `"room"`, `"rent"`, `"ped"` substring matches in `api.ts:175-179` trigger wrong mock answers. | 🔴 CRITICAL |
| 6 | Graceful Gemini fallback | Raises `GeminiUnavailableError` instead of "partial summary". `FALLBACK_SUMMARIES` dict is dead code. | 🟠 HIGH |
| 7 | `degraded_mode` signal | No `is_fallback` or `degraded_mode` field in any API response schema. Frontend cannot know it's serving degraded data. | 🟠 HIGH |
| 8 | RAG retrieval | Uses lexical keyword overlap (`_lexical_similarity`) — not pgvector. 384-dim embeddings stored in Supabase are never queried by RAG. | 🔴 CRITICAL |
| 9 | Scraper seed URLs | All 8 URLs are deep PDF links — not verified; most likely return 403/404. No live HTTP check before use. | 🔴 CRITICAL |
| 10 | Webhook handlers | Both webhooks return hardcoded stubs; no DB updates, no cache invalidation, no re-analysis queued. | 🟠 HIGH |
| 11 | Benchmark data freshness | `last_scraped_at = datetime.utcnow()` always — data always appears "just scraped" regardless of actual age. | 🟠 HIGH |
| 12 | "500" substring in error classifier | `"500" in err_str` at `gemini_client.py:140` falsely classifies prompt-length errors as transient HTTP 500. | 🟡 MEDIUM |
| 13 | Amber "not found" chat state | Backend returns correct text but frontend renders it identically to a normal answer — no amber visual distinction. | 🟡 MEDIUM |
| 14 | Low-OCR-quality warning | No flag in API response when OCR quality is poor; garbled placeholder text presented as real content. | 🟡 MEDIUM |

---

## Priority Order for Remaining Work

Ordered by impact on the core demo flow (upload → summary → red flags → chat → compare):

1. 🔴 **Install Tesseract** + set `TESSERACT_CMD` env var — scanned PDFs currently return placeholder text
2. 🔴 **Fix ChromaDB/protobuf conflict** (`pip install "protobuf<4.0.0"`) — embeddings are fake until fixed
3. 🔴 **Wire ML trigger from ingestion** (`pipeline.py` step 6) — no document ever reaches `analyzed` status
4. 🔴 **Replace RAG lexical search with pgvector query** — the HNSW index exists; it just isn't used
5. 🔴 **Add `is_fallback`/`degraded_mode` to all API response schemas** — frontend is blind to degraded state
6. 🔴 **Fix mock fallback substring bugs** in `api.ts:175-179` — `"current"` → room-rent mock is the "emi/premium" bug class
7. 🔴 **Verify and replace seed URLs** with real HTTP-confirmed hub pages
8. 🔴 **LLM confirmation step** for red-flag detection — `confirmed_by_llm=True` is a data integrity lie
9. 🟠 **Remove silent mock fallback** or make it visually distinct (amber banner "Demo Mode — backend unavailable")
10. 🟠 **Wire real benchmark penalty** into confidence score from `benchmark_products` table
11. 🟠 **Add language toggle UI** — backend already supports `language=hi`
12. 🟠 **Implement real JWT auth** — currently any `user_id` is accepted
13. 🟠 **Add PII redaction** before Gemini calls
14. 🟠 **Build n8n `scrape-benchmarks` workflow** — the entire benchmark pipeline depends on it
