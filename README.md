# Money Docs Decoded

Plain-language financial document analyzer, red-flag detector, and benchmark intelligence platform.

## Repository Architecture (Monorepo)

- /frontend: Next.js web application for document upload, interactive summary dashboards, citation viewer, and Q&A chat.
- /backend: FastAPI orchestrator and API layer handling ingestion pipelines, ML/LLM services, knowledge base queries, and n8n webhook callbacks.
- /scraper: Scraper microservice fetching public policy wordings, fee schedules, and ombudsman reports into benchmark tables.
- /n8n: Exported workflow JSON definitions for asynchronous automations and scheduled tasks.
- /docs: Component specifications, architecture blueprints, and design systems.
- /tests: Integration and contract verification test suites.

## Getting Started

1. Copy .env.example to .env and fill in necessary configuration keys (Sarvam AI, Supabase, n8n webhook secret).
2. Set up backend:
   `ash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   `
3. Database Migrations:
   Apply /backend/migrations/001_initial_schema.sql to your Supabase / PostgreSQL instance.
