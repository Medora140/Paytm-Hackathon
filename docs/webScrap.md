# Web Scraping & Competitive Intelligence — Component Spec

**Role:** It lets the product go beyond "explain the document I uploaded" into "tell me how this document's terms compare to what's publicly available," by scraping insurer/lender-published policy wordings, fee schedules, and public complaint data. This is what powers the `/doc/[id]/compare` page and the benchmark strip on the summary page.

**Important framing:** this component produces *benchmark context*, not a claim about "the truth." Public policy pages, brochures, and fee schedules change, get versioned, and sometimes don't match the exact policy variant a user holds. Every scraped fact shown to a user must carry a source link and a last-scraped timestamp — this is a legal-exposure and trust issue, not just a UX nicety.

## What it scrapes

1. **Publicly posted policy wordings / key-feature documents (KFDs)** from insurer websites — most Indian insurers publish these as PDFs (e.g., "Download Policy Wording" links). These are the highest-value, lowest-legal-risk target since insurers publish them precisely to be read publicly.
2. **Fee/charge schedules** — processing fee, prepayment penalty tables for lenders; expense ratio/exit load tables for mutual funds — often published as static tables or PDFs on the issuer's site.
3. **Public regulator data** — IRDAI's published Ombudsman annual reports, RBI's Banking Ombudsman Scheme reports, and any public grievance/complaint statistics by insurer. This is the "real ombudsman dispute data" the pitch deck references — it must come from these public regulator sources, not be invented.
4. **(Stretch, higher legal risk — deprioritize)** Third-party review/aggregator sites. Scraping these needs more care around ToS and copyright; start without this and add only if time and legal comfort allow.

## Architecture

```
n8n scheduled trigger (e.g., weekly)
   │
   ▼
Scraper workers (Python: requests/httpx + BeautifulSoup, or Playwright for JS-heavy pages)
   │
   ├──► robots.txt / ToS check gate (skip + log if disallowed)
   ├──► Fetch page/PDF → extract structured fields (reuse the ingestion service's
   │     PDF/text extraction from 03-ml-ai-engine.md — don't build a second parser)
   ├──► Normalize into a common schema per product category
   ▼
`benchmark_products` table (Postgres) — versioned, timestamped
   │
   ▼
Backend `/documents/{id}/compare` endpoint reads from this table (never scrapes live on request)
```

## Scope-limiting decisions

- **Do NOT build an open-ended "crawl the whole internet for any company" scraper for the hackathon.**
- **Start with a hardcoded seed list** of 5–10 major Indian insurers'/lenders' public policy-document pages (e.g., their "Download Policy Wording" or "Key Features Document" sections), matched to the document types you support at launch (health insurance first).
- **Category-based matching, not exact-company matching, as a fallback:** if the user's specific issuer isn't in your seed list, show comparables from the same product category with a clear label ("General market comparison — issuer not in our benchmark set yet") rather than failing silently or guessing.
- **Respect robots.txt and each site's terms of use** before scraping; log and skip sources that disallow it. Prefer sources that are *designed* to be publicly downloaded (regulatory filings, published KFDs) over pages that actively resist scraping — this is both the safer and the higher-quality data source.

## Common normalized schema (`benchmark_products` table, conceptual)

```
{
  product_category: "health_insurance" | "personal_loan" | "mutual_fund",
  issuer_name: string,
  product_name: string,
  source_url: string,
  last_scraped_at: timestamp,
  attributes: {
     // insurance example
     room_rent_cap: "...",
     waiting_period_pre_existing: "...",
     co_pay_percent: "...",
     premium_range: "...",
     claim_settlement_ratio: "..."   // from public IRDAI disclosures if available
  },
  complaint_signal: {
     source: "IRDAI Ombudsman Annual Report 2024",
     complaints_per_10k_policies: number | null
  }
}
```

## How this connects to the red-flag detector

The scraped `complaint_signal` and category-level attribute distributions feed two things back into `03-ml-ai-engine.md`:
1. **Benchmark penalty** in the confidence-score formula (e.g., "this room-rent cap is stricter than 80% of scraped comparables → deduct points").
2. **New red-flag pattern candidates** — if a clause type shows up disproportionately in ombudsman complaint data for a category, it's a strong candidate to add to the Red-Flag Knowledge Base, closing the loop between "what the web says causes disputes" and "what we flag in your document."

## Failure modes to design for

- **Source page changes/breaks:** each scraper job should fail gracefully per-source (log + skip), not fail the whole batch.
- **Stale data:** always surface `last_scraped_at` to the user; if a source hasn't refreshed in >30 days, mark it "possibly outdated" rather than presenting it as current.
- **No comparable found:** the compare page must have an explicit empty state ("Not enough public data yet to benchmark this product") — never fabricate a comparison.

## Ownership boundary

This component **produces and refreshes data only** — it does not call the LLM to reason about a specific user's document, and it does not run synchronously inside a user's request. It is triggered and scheduled by n8n (see `06-n8n-automation-workflows.md`) and exposes its output only through the `benchmark_products` table that the backend reads.