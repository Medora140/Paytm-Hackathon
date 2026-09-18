# n8n Orchestration — Component Spec

**Role:** n8n owns *scheduled and asynchronous* workflows that don't need to sit in the user-facing request path. The rule of thumb: **if a user is waiting for it, it belongs in the backend; if it runs on a timer or reacts to an event nobody is waiting on, it belongs in n8n.**

## Why n8n here specifically

- Keeps scraping schedules, retries, and error-notification logic out of your core backend code, so the backend stays focused on the request/response API.
- Gives you a visual, demoable "automation" story for judges — you can literally show a workflow diagram of the scraping/refresh pipeline, which reinforces the "production-grade" positioning.
- Handles the kind of glue work (webhook → transform → conditional → notify) that would otherwise be boilerplate backend code.

## Workflows to build

### 1. Scheduled benchmark scraping (`scrape-benchmarks`)
**Trigger:** Cron (e.g., weekly).
**Steps:**
1. Read the seed list of source URLs (from a config table or n8n's own credential/variable store).
2. For each source: HTTP request node → check robots.txt/ToS gate → extract/parse (call out to your Python scraper microservice via HTTP node, rather than trying to do heavy parsing in n8n itself — n8n orchestrates, it doesn't replace your scraping code).
3. On success: POST normalized data to backend's internal ingestion endpoint for `benchmark_products`.
4. On failure: log to `scrape_jobs` via backend webhook, and if failures exceed a threshold, send a Slack/email alert to the team.
5. Call `POST /webhooks/n8n/scrape-complete` so the backend can invalidate any stale compare-page caches.

### 2. Document re-analysis trigger (`re-analyze-on-kb-update`)
**Trigger:** Webhook, fired when the Red-Flag Knowledge Base is updated (new pattern added).
**Steps:**
1. Query backend for all documents analyzed with an older `kb_version`.
2. Batch-queue re-analysis jobs (respecting rate limits — don't blast the LLM API with every document at once; throttle with n8n's built-in batching/wait nodes).
3. Notify affected users only if their score materially changed (avoid spamming notifications for cosmetic re-runs).

### 3. Async OCR/heavy-ingestion overflow (`ocr-overflow-queue`)
**Trigger:** Webhook from backend when a document is large/scanned and OCR is expected to take >X seconds.
**Steps:**
1. Backend hands off the job to n8n instead of blocking the request.
2. n8n calls the OCR service, waits/polls, then calls back `POST /webhooks/n8n/scrape-complete`-style endpoint (or a dedicated `/webhooks/n8n/ingestion-complete`) with the result.
3. This keeps your FastAPI backend from holding long-lived connections open for slow OCR jobs.

### 4. New-source discovery (stretch goal) (`discover-new-sources`)
**Trigger:** Manual or monthly cron.
**Steps:**
1. Search for newly published insurer/lender policy-document pages (e.g., via a search API node).
2. Surface candidates to a human (Slack approval step) before adding to the scrape seed list — keep a human in the loop rather than auto-expanding scraping targets, both for legal safety and data quality.

### 5. Ops/health alerting (`pipeline-health-alerts`)
**Trigger:** Webhook or scheduled check.
**Steps:**
1. Poll backend's `/admin` health summary (documents stuck in a status for too long, scrape job failure rate, LLM error rate).
2. Alert the team (Slack/email) if thresholds are breached — this is what keeps a live demo from silently failing.

## What n8n explicitly does NOT own

- No direct LLM reasoning calls that are part of a live user request (chat, summary-on-upload) — those stay in the backend for latency and error-handling control.
- No direct database writes to user-facing tables — n8n talks to the backend's internal/webhook endpoints, which enforce validation and keep the backend as the single source of truth for data integrity.