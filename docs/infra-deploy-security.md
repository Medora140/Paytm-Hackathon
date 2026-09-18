# Infrastructure, Deployment & Security — Component Spec


<!-- ## Hosting (hackathon-realistic choices)

| Piece | Suggestion | Why |
|---|---|---|
| Frontend | Vercel | Zero-config Next.js deploys, instant preview URLs for judges |
| Backend API | Railway or Render | Fast to deploy FastAPI, easy env-var/secrets management |
| Database + Auth + Storage | Supabase | Postgres + pgvector + Auth + Storage in one managed service — minimizes integration surface |
| n8n | n8n Cloud, or a small Railway/Docker instance | You already have it wired to Antigravity as MCP — keep it reachable via a stable webhook URL |
| LLM | Gemini API (free tier) | You're already using a free Gemini API key for this project |
| Scraper workers | Same backend host or a small separate worker service, triggered by n8n | Keep isolated so a scraping failure can't take down the user-facing API | -->

## Secrets & configuration

- All API keys (Gemini, OCR provider, Supabase service key)live in environment variables per deployment platform — never committed to the repo.
n8n is put as an MCP server.
- n8n → backend webhooks should be authenticated with a shared secret header, not left open — anyone who finds the webhook URL should not be able to inject fake scrape data or trigger re-analysis storms.

## Authentication & authorization

- Use Supabase Auth or Clerk rather than building custom auth — not a differentiator for this product, and rolling your own auth is the most common source of hackathon-project security holes.
- Every document-scoped backend endpoint must verify `document.user_id == current_user.id` — a document should never be readable by a user who didn't upload it.

## Privacy & compliance (India-specific — this matters for a Paytm-track project)

- **DPDP Act 2023 alignment:** implement "right to erasure" for real (cascade-delete on `DELETE /documents/{id}`, not a soft flag that leaves data queryable), a clear consent statement on upload about what's done with the file, and data retention limits (e.g., auto-delete raw files after N days unless the user opts to keep them).
- **Sensitive personal data:** health insurance documents may contain health information — treat this as sensitive personal data under DPDP, meaning stricter consent and handling requirements than generic app data.
- **Third-party LLM transmission:** be explicit in your privacy copy that document content is sent to Google's Gemini API for processing — don't leave this undisclosed. This matters more than usual with a free-tier key specifically: under Gemini API's current terms, free/unpaid-tier usage allows Google to use your prompts and responses (including uploaded content) to improve its products, and human reviewers may read that data — the paid tier does not do this. For a product handling real users' health/financial documents, this is worth disclosing explicitly in your privacy copy, and worth budgeting for a move to the paid tier before handling real (non-demo/non-synthetic) user documents.
- **Disclaimer requirement:** every AI-generated output (summary, red flag, score, chat answer) must be clearly marked as informational, not professional financial/legal/insurance advice — this is both an ethical requirement and a real liability shield.

## Observability

- Structured logging (JSON logs) on the backend, tagged with `document_id`/`user_id`/pipeline stage, so a failure during the live demo can be diagnosed in seconds, not minutes.
- Minimal uptime/error dashboard (even a simple `/admin` page reading from `scrape_jobs` and `documents.status` counts, as noted in `01-frontend.md`) beats having zero visibility into pipeline health during a judged demo.

## Security checklis

- [ ] File upload size/type validation (reject non-PDF/image, cap file size) to prevent abuse.
- [ ] Rate limiting on `/chat` and `/documents` endpoints (per-user) to prevent runaway LLM costs from a single bad actor or bug.
- [ ] HTTPS everywhere (default on Vercel/Railway/Supabase, just confirm no mixed-content warnings).
- [ ] Scraper respects robots.txt/ToS (see `04-web-scraping-intelligence.md`) — a judge or issuer noticing scraping misuse is a reputational risk worth avoiding.
- [ ] No API keys or Supabase service-role keys ever shipped in frontend bundle — only anon/public keys client-side.