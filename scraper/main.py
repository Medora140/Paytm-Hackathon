"""
Money Docs Decoded - Competitive Intelligence Scraper Worker
Executes scheduled benchmark scraping jobs triggered by n8n or CLI.
Enforces robots.txt compliance, normalizes extracted facts into
benchmark_products, and logs job statuses in scrape_jobs table.
"""

import sys
import os
import argparse
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scraper.robots_guard import RobotsGuard
from scraper.extractor import extract_mutual_fund_facts, normalize_to_benchmark_product
from scraper.seed_urls import SEED_BENCHMARK_SOURCES

try:
    from backend.app.scraping.repository import ScrapeRepository
except ImportError:
    try:
        from app.scraping.repository import ScrapeRepository
    except ImportError:
        ScrapeRepository = None

logger = logging.getLogger("ScraperWorker")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass
class ScrapeJobResult:
    url: str
    status: str  # 'success' | 'failed' | 'skipped_robots'
    product_name: str
    issuer_name: str
    job_id: Optional[str] = None
    error_message: Optional[str] = None
    extracted_product_id: Optional[str] = None


def fetch_document_content(url: str, timeout_sec: float = 15.0) -> bytes:
    """Fetches PDF or HTML document bytes over HTTP."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MoneyDocsDecodedBot/1.0",
        "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    with httpx.Client(timeout=timeout_sec, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.content


def extract_facts_from_content(content: bytes, seed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts structured attributes from raw PDF bytes or HTML text.
    """
    text = ""
    # Check if PDF content
    if content.startswith(b"%PDF-") or seed.get("doc_format") == "pdf":
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            # Extract first 10 pages for factsheet summaries
            page_texts = []
            for i in range(min(10, len(doc))):
                page_texts.append(doc[i].get_text("text"))
            doc.close()
            text = "\n".join(page_texts)
        except Exception as e:
            logger.warning(f"PyMuPDF parse error for {seed.get('product_name')}: {e}")
            text = ""

    if not text:
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

    facts = extract_mutual_fund_facts(
        text=text,
        issuer_name=seed.get("issuer_name", "Unknown Mutual Fund"),
        product_name=seed.get("product_name", "Mutual Fund Scheme"),
        source_url=seed.get("source_url", "")
    )
    return normalize_to_benchmark_product(facts)


def run_single_scrape(
    seed: Dict[str, Any],
    repository: Any,
    guard: RobotsGuard,
    triggered_by: str = "manual"
) -> ScrapeJobResult:
    """
    Runs a single source scrape with robots.txt gate and per-source error containment.
    """
    url = seed.get("source_url", "")
    product_name = seed.get("product_name", "Unknown")
    issuer_name = seed.get("issuer_name", "Unknown")

    # Step 1: Create pending job record in scrape_jobs
    job_id = repository.create_scrape_job(
        source_url=url,
        triggered_by=triggered_by,
        status="pending"
    )

    # Step 2: Robots.txt gate check
    if not guard.can_fetch(url):
        reason = "Disallowed by publisher robots.txt policy"
        logger.info(f"[ROBOTS GATE] Skipping disallowed URL: {url}")
        repository.update_scrape_job(job_id=job_id, status="skipped_robots", error_message=reason)
        return ScrapeJobResult(
            url=url,
            status="skipped_robots",
            product_name=product_name,
            issuer_name=issuer_name,
            job_id=job_id,
            error_message=reason
        )

    # Step 3: Fetch document and extract structured attributes
    try:
        logger.info(f"[FETCH] Retrieving source document: {url}")
        content = fetch_document_content(url)
        normalized_product = extract_facts_from_content(content, seed)

        # Step 4: Persist to benchmark_products table
        saved = repository.save_benchmark_product(normalized_product)
        product_id = saved.get("id")

        # Step 5: Mark scrape_jobs record as success
        repository.update_scrape_job(job_id=job_id, status="success")
        logger.info(f"[SUCCESS] Scraped and normalized {product_name} ({issuer_name}) -> id: {product_id}")

        return ScrapeJobResult(
            url=url,
            status="success",
            product_name=product_name,
            issuer_name=issuer_name,
            job_id=job_id,
            extracted_product_id=product_id
        )

    except Exception as exc:
        err_msg = f"Extraction failed: {type(exc).__name__}: {str(exc)}"
        logger.error(f"[FAILURE] Error scraping {url}: {err_msg}")
        # Failure isolation: update job record and return failed status without throwing
        repository.update_scrape_job(job_id=job_id, status="failed", error_message=err_msg)
        return ScrapeJobResult(
            url=url,
            status="failed",
            product_name=product_name,
            issuer_name=issuer_name,
            job_id=job_id,
            error_message=err_msg
        )


def run_batch_scrape(
    seeds: Optional[List[Dict[str, Any]]] = None,
    repository: Optional[Any] = None,
    triggered_by: str = "n8n_weekly_schedule"
) -> List[ScrapeJobResult]:
    """
    Executes batch scrape across all seed URLs.
    Ensures per-source failure isolation so a failing URL does not crash the batch.
    """
    target_seeds = seeds or SEED_BENCHMARK_SOURCES
    repo = repository or ScrapeRepository()
    guard = RobotsGuard(user_agent="MoneyDocsDecodedBot/1.0")

    logger.info(f"Starting batch scrape for {len(target_seeds)} benchmark sources (triggered_by={triggered_by})")
    results: List[ScrapeJobResult] = []

    for seed in target_seeds:
        result = run_single_scrape(
            seed=seed,
            repository=repo,
            guard=guard,
            triggered_by=triggered_by
        )
        results.append(result)

    success_count = sum(1 for r in results if r.status == "success")
    skipped_count = sum(1 for r in results if r.status == "skipped_robots")
    failed_count = sum(1 for r in results if r.status == "failed")
    logger.info(f"Batch completed: {success_count} succeeded, {skipped_count} skipped (robots.txt), {failed_count} failed")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Money Docs Decoded Scraper Worker")
    parser.add_argument("positional_url", nargs="?", help="Optional positional target URL", default=None)
    parser.add_argument("--url", help="Scrape a single target URL directly", default=None)
    parser.add_argument("--issuer", help="Issuer name for single URL scrape", default="Custom Issuer")
    parser.add_argument("--product", help="Product name for single URL scrape", default="Custom Scheme")
    parser.add_argument("--trigger", help="Trigger source id (e.g. n8n workflow)", default="cli_manual")
    args = parser.parse_args()

    repo = ScrapeRepository()
    target_url = args.url or args.positional_url
    if target_url:
        seeds = [{
            "issuer_name": args.issuer,
            "product_name": args.product,
            "product_category": "mutual_fund",
            "source_url": target_url,
            "doc_format": "pdf" if target_url.endswith(".pdf") else "html"
        }]
        res = run_batch_scrape(seeds=seeds, repository=repo, triggered_by=args.trigger)
        print(res)
    else:
        results = run_batch_scrape(repository=repo, triggered_by=args.trigger)
        for r in results:
            print(f"[{r.status.upper()}] {r.issuer_name} - {r.product_name} ({r.url})")
