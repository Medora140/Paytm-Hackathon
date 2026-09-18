# Web Scraper Microservice

Microservice responsible for competitive intelligence scraping of public insurer & lender policy wordings, fee schedules, and IRDAI/RBI ombudsman complaint datasets.

## Architecture Boundary
- Produces and refreshes data only (writes to enchmark_products in Supabase).
- Does not run live synchronously inside user requests.
- Triggered and orchestrated on schedule by n8n.
