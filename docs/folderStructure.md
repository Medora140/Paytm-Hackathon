# Architecture — How the Pieces Fit


User (Browser)
   │
   ▼
Frontend — Next.js (App Router) + TypeScript + Tailwind  [port 3000]
   │  └── Calls backend via REST API (fetch + Supabase session token)
   │
   ▼
Backend — FastAPI (Python)  [port 8000]
   │
   ├──► Ingestion Pipeline    (OCR → chunking → embeddings → Supabase)
   ├──► ML / AI Engine        (Gemini API → summary / red-flags / chat)
   ├──► Scraping Service      (reads benchmark_products from Supabase)
   ├──► n8n Webhooks          (receives scrape-complete / kb-updated callbacks)
   └──► Supabase              (PostgreSQL + pgvector + Auth)
          └── 10 tables: users, documents, document_chunks, document_summaries,
                         red_flags, red_flag_patterns, confidence_scores,
                         chat_messages, benchmark_products, scrape_jobs
Scraper Microservice — Python (httpx + BeautifulSoup)
   └── Triggered by n8n cron → writes to benchmark_products
n8n (Cloud / Docker)
   └── Orchestrates: scheduled scraping, async jobs, alerts

#  Folder Structure


money-docs-decoded/                    ← Monorepo root
│
├── .env                               ← Active secrets (Gemini, Supabase, n8n)
├── .env.example                       ← Template with all required keys
├── .gitignore
├── package.json                       ← Root-level (minimal, workspace glue)
├── ORIGINAL_REQUEST.md                ← Agent task history & known issues log
├── README.md
│
├── docs/                              ← All specification documents
│   ├── architecture.md
│   ├── frontEnd.md
│   ├── backEnd.md
│   ├── aiEngine.md
│   ├── database.md
│   ├── webScrap.md
│   ├── n8n.md
│   ├── infra-deploy-security.md
│   ├── design.md
│   └── feature_audit_report.md        ← Previous audit (now updated by this session)
│
├── frontend/                          ← Next.js web application
│   ├── .env
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── vitest.config.ts
│   ├── vitest.setup.ts
│   │
│   └── src/
│       ├── app/                       ← Next.js App Router pages
│       │   ├── layout.tsx             ← Root layout (DisclaimerBanner + Navigation + Footer)
│       │   ├── page.tsx               ← Landing page  /
│       │   ├── globals.css
│       │   │
│       │   ├── upload/
│       │   │   └── page.tsx           ← Upload page  /upload
│       │   │
│       │   ├── doc/
│       │   │   └── [id]/
│       │   │       ├── page.tsx       ← Document Dashboard  /doc/[id]
│       │   │       ├── chat/
│       │   │       │   └── page.tsx   ← Q&A Chat  /doc/[id]/chat
│       │   │       └── compare/
│       │   │           └── page.tsx   ← Benchmark Compare  /doc/[id]/compare
│       │   │
│       │   ├── documents/
│       │   │   └── page.tsx           ← History / My Documents  /documents
│       │   │
│       │   ├── settings/
│       │   │   └── page.tsx           ← Settings  /settings
│       │   │
│       │   ├── admin/
│       │   │   └── page.tsx           ← Admin Dashboard  /admin
│       │   │
│       │   ├── login/
│       │   │   └── page.tsx           ← Login  /login
│       │   │
│       │   └── signup/
│       │       └── page.tsx           ← Sign Up  /signup
│       │
│       ├── components/                ← Reusable UI components
│       │   ├── Navigation.tsx         ← Sticky nav, language toggle, doc switcher, auth
│       │   ├── DisclaimerBanner.tsx   ← Global compliance disclaimer
│       │   ├── UploadForm.tsx         ← Drag-drop upload, doc type selector, stage progress
│       │   ├── ConfidenceScoreWidget.tsx  ← Score ring + color + breakdown
│       │   ├── SummaryCard.tsx        ← Plain-language bullets by category
│       │   ├── RedFlagsPanel.tsx      ← Flagged clauses with severity + citations
│       │   ├── BenchmarkStrip.tsx     ← Market comparison strip on dashboard
│       │   └── SkeletonLoader.tsx     ← Skeleton states for loading screens
│       │
│       ├── lib/
│       │   ├── api.ts                 ← All fetch calls to backend (with mock fallback)
│       │   ├── mockData.ts            ← Demo/fallback data constants
│       │   └── supabaseClient.ts      ← Supabase JS client (anon key, auth session)
│       │
│       ├── types/                     ← Shared TypeScript interfaces
│       │
│       └── __tests__/                 ← Frontend test files
│
├── backend/                           ← FastAPI Python application
│   ├── .env
│   ├── requirements.txt
│   ├── __init__.py
│   │
│   ├── app/                           ← Main application package
│   │   ├── main.py                    ← FastAPI app, CORS, router registration, error handlers
│   │   ├── auth.py                    ← JWT Bearer dependency (get_current_user)
│   │   ├── db.py                      ← Supabase client init + StubSupabaseClient
│   │   ├── schemas.py                 ← Pydantic request/response models
│   │   ├── errors.py                  ← Custom exceptions (ChunksNotFoundError, GeminiUnavailableError)
│   │   ├── identity.py                ← Demo user constants
│   │   ├── runtime_flags.py           ← running_under_pytest(), allow_in_memory_stores()
│   │   │
│   │   ├── routers/                   ← API route handlers
│   │   │   ├── auth.py                ← /auth/signup, /auth/login, /auth/me, /auth/session
│   │   │   ├── ingestion.py           ← POST/GET/DELETE /documents, GET /documents/{id}
│   │   │   ├── ml.py                  ← GET summary/red-flags/confidence-score, POST chat
│   │   │   ├── scraping.py            ← GET /documents/{id}/compare
│   │   │   └── webhooks.py            ← POST /webhooks/n8n/scrape-complete & kb-updated
│   │   │
│   │   ├── ingestion/                 ← Document ingestion pipeline
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py            ← Orchestrator (7 stages: upload→extract→chunk→embed→analyze)
│   │   │   ├── detector.py            ← Native vs. scanned PDF detection
│   │   │   ├── extractor.py           ← pypdf + PyMuPDF + Tesseract OCR
│   │   │   ├── chunker.py             ← Clause-level semantic chunker with page tags
│   │   │   ├── embedder.py            ← SentenceTransformer MiniLM-L6-v2 (384-dim)
│   │   │   ├── storage.py             ← File storage manager (local filesystem)
│   │   │   └── repository.py          ← documents + document_chunks CRUD (Supabase + in-memory fallback)
│   │   │
│   │   ├── ml/                        ← AI / ML engine
│   │   │   ├── __init__.py
│   │   │   ├── service.py             ← MLService orchestrator (get_summary, get_red_flags, chat)
│   │   │   ├── gemini_client.py       ← Live connectivity probe, model failover, generate_gemini_content()
│   │   │   ├── summary_generator.py   ← Gemini structured summary (per-doc-type prompts, EN/HI)
│   │   │   ├── red_flag_detector.py   ← Rule-based keyword + regex flag detector with citations
│   │   │   ├── knowledge_base.py      ← Hardcoded Red-Flag KB (15+ SEBI/IRDAI/RBI patterns)
│   │   │   ├── confidence_score.py    ← Transparent formula: 100 - severity weights ± adjustments
│   │   │   ├── rag_chat.py            ← RAG chat: embed query → cosine similarity → Gemini generation
│   │   │   └── mock_data.py           ← Chunk resolver: Supabase query → raises ChunksNotFoundError if empty
│   │   │
│   │   └── scraping/                  ← Benchmark scraping service
│   │       ├── __init__.py
│   │       ├── models.py              ← BenchmarkProduct dataclass
│   │       ├── repository.py          ← benchmark_products CRUD (Supabase)
│   │       └── service.py             ← BenchmarkService: category-based comparisons + fallback data
│   │
│   ├── migrations/                    ← Supabase SQL migrations
│   │   ├── 001_initial_schema.sql     ← All 10 tables + indexes + HNSW vector index
│   │   └── 002_vector_search_function.sql  ← pgvector similarity search function
│   │
│   ├── tests/                         ← Backend test files
│   ├── models/                        ← (additional model assets folder)
│   ├── storage/                       ← Local file storage (uploaded PDFs)
│   ├── data/                          ← Reference data
│   ├── core/                          ← Core utilities
│   ├── experiments/                   ← Experimental scripts
│   └── [many check_*.py / test_*.py]  ← Diagnostic/debug scripts from prior agent runs
│
├── scraper/                           ← Standalone scraper microservice
│   ├── __init__.py
│   ├── main.py                        ← Worker entry point (CLI + n8n trigger)
│   ├── robots_guard.py                ← robots.txt compliance checker
│   ├── extractor.py                   ← HTML/PDF fact extraction + normalization
│   ├── seed_urls.py                   ← Hardcoded seed URLs (mutual fund sources)
│   └── README.md
│
├── n8n/                               ← n8n workflow definitions
│   ├── scrape-benchmarks.json         ← Exported scrape-benchmarks workflow
│   └── README.md
│
└── tests/                             ← Root-level integration tests

## Key observation: The backend/ root contains ~40 check_*.py and test_*.py diagnostic scripts from prior agent debugging runs — these are not part of the application, just artefacts left behind by previous agents.