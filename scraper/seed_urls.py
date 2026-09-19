"""
Hardcoded seed list of public mutual fund factsheet hub/index pages.

All URLs in SEED_BENCHMARK_SOURCES were personally verified with HTTP GET
requests (timeout=10s, follow_redirects=True) and returned HTTP 200 in this
session (2026-09-18).

Design choices:
- We use HUB/INDEX pages rather than deep PDF links. Deep PDF links break
  when AMCs update their factsheets monthly; hub pages are stable and let
  the n8n HTML-Extract step dynamically discover current PDF URLs.
- Any URL that returned non-200 is excluded and documented in comments below.
- AMFI portal is included as the primary regulatory data source.

EXCLUDED URLS (non-200 in testing — do not re-add without re-verification):
  # HDFC direct PDF: 403 Forbidden
  # "https://www.hdfcfund.com/content/dam/hdfc-amc/factsheet/HDFC_MF_Handbook_Aug_2024.pdf"
  # HDFC Factsheets hub: 403 Forbidden
  # "https://www.hdfcfund.com/mutual-funds/factsheets"
  # SBI Bluechip PDF: 404 Not Found
  # "https://www.sbimf.com/en-us/downloads/factsheets/sbi-bluechip-fund-factsheet.pdf"
  # SBI MF Downloads hub: 404 Not Found
  # "https://www.sbimf.com/en-us/downloads"
  # ICICI Pru direct PDF: DNS resolution failure (getaddrinfo failed)
  # "https://www.icicipruamc.com/downloads/factsheets/icici-pru-bluechip-factsheet.pdf"
  # Nippon India Large Cap direct PDF: 404 Not Found
  # "https://mf.nipponindiaim.com/InvestorServices/FactSheets/NipponIndia-Large-Cap-Factsheet.pdf"
  # Nippon India FactSheet.aspx: 404 Not Found
  # "https://mf.nipponindiaim.com/FundsAndPerformance/Pages/FactSheet.aspx"
  # PPFAS direct PDF: 404 Not Found
  # "https://amc.ppfas.com/schemes/parag-parikh-flexi-cap-fund/factsheet.pdf"
  # Kotak direct PDF: 404; Kotak hub redirects to Radware bot-protection — EXCLUDED
  # "https://www.kotakmf.com/downloads/factsheets/kotak-emerging-equity-factsheet.pdf"
  # UTI direct PDF: 200 but returns text/html (not a PDF) — not a real PDF
  # "https://www.utimf.com/downloads/factsheets/uti-nifty-50-index-factsheet.pdf"
"""

import httpx
from typing import List, Dict, Any


def check_url(url: str, timeout: float = 10.0) -> bool:
    """
    Verify a URL is reachable and returns HTTP 200.

    Args:
        url: The URL to test.
        timeout: Request timeout in seconds (default 10s).

    Returns:
        True if the URL returns status 200, False otherwise.

    Example:
        >>> check_url("https://portal.amfiindia.com")
        True
        >>> check_url("https://www.hdfcfund.com/mutual-funds/factsheets")
        False  # returns 403
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
    }
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            resp = client.get(url)
            return resp.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Verified seed sources — all returned HTTP 200 on 2026-09-18.
# All are hub/index pages so the n8n HTML-Extract node can discover
# current PDF links dynamically rather than hard-coding fragile deep URLs.
# ---------------------------------------------------------------------------
SEED_BENCHMARK_SOURCES: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------
    # AMFI — primary Indian regulatory/data authority for mutual funds.
    # Returns 200; frameset page linking to NAV data, scheme lists, etc.
    # ------------------------------------------------------------------
    {
        "issuer_name": "AMFI India (Regulatory)",
        "product_name": "AMFI Mutual Fund Portal",
        "product_category": "mutual_fund",
        "source_url": "https://portal.amfiindia.com",
        "doc_format": "hub",
        "page_type": "regulatory_hub",
        "verified_status": 200,
        "notes": (
            "AMFI regulatory portal — verified HTTP 200. "
            "Primary authoritative source for all Indian MF scheme data. "
            "Use DownloadSchemeData_Po.aspx?mf=0 for NAV CSV (also 200, ~4MB)."
        ),
    },
    {
        "issuer_name": "AMFI India (Regulatory)",
        "product_name": "AMFI All-Scheme NAV Data (CSV)",
        "product_category": "mutual_fund",
        "source_url": "https://portal.amfiindia.com/DownloadSchemeData_Po.aspx?mf=0",
        "doc_format": "csv",
        "page_type": "regulatory_data",
        "verified_status": 200,
        "notes": (
            "AMFI NAV data for all schemes — verified HTTP 200, text/csv, ~4MB. "
            "Direct machine-readable data; scraper can parse NAV/returns directly."
        ),
    },
    # ------------------------------------------------------------------
    # ICICI Prudential AMC — downloads hub returns 200, 18KB HTML.
    # ------------------------------------------------------------------
    {
        "issuer_name": "ICICI Prudential Mutual Fund",
        "product_name": "ICICI Prudential AMC Downloads Hub",
        "product_category": "mutual_fund",
        "source_url": "https://www.icicipruamc.com/downloads",
        "doc_format": "hub",
        "page_type": "amc_downloads_hub",
        "verified_status": 200,
        "notes": (
            "ICICI Pru AMC downloads hub — verified HTTP 200, 18KB HTML. "
            "Use HTML Extract / Playwright to discover current factsheet PDF links. "
            "Direct PDF URL was DNS-unresolvable; this hub is the stable entry point."
        ),
    },
    # ------------------------------------------------------------------
    # Mirae Asset AMC — factsheet hub returns 200, 143KB HTML with PDFs.
    # The deep PDF URL 302-redirected to this hub (AMCs update monthly).
    # ------------------------------------------------------------------
    {
        "issuer_name": "Mirae Asset Mutual Fund",
        "product_name": "Mirae Asset Factsheet Downloads Hub",
        "product_category": "mutual_fund",
        "source_url": "https://www.miraeassetmf.co.in/downloads/factsheet",
        "doc_format": "hub",
        "page_type": "amc_factsheet_hub",
        "verified_status": 200,
        "notes": (
            "Mirae Asset factsheet hub — verified HTTP 200, 143KB HTML with PDF links. "
            "Original deep PDF URL redirected here. Hub contains static PDF links. "
            "Playwright recommended as some content is JS-rendered."
        ),
    },
    # ------------------------------------------------------------------
    # PPFAS (Parag Parikh) AMC — scheme hub returns 200 with live PDF links.
    # ------------------------------------------------------------------
    {
        "issuer_name": "PPFAS Mutual Fund",
        "product_name": "Parag Parikh Flexi Cap Fund — Scheme Hub",
        "product_category": "mutual_fund",
        "source_url": "https://amc.ppfas.com/schemes/parag-parikh-flexi-cap-fund/",
        "doc_format": "hub",
        "page_type": "amc_scheme_hub",
        "verified_status": 200,
        "notes": (
            "PPFAS scheme hub — verified HTTP 200, 131KB HTML with live PDF links. "
            "Contains factsheet PDFs hosted on amc.ppfas.media CDN. "
            "Original factsheet.pdf path was 404; this hub has current links."
        ),
    },
    # ------------------------------------------------------------------
    # Nippon India AMC — investor-services/downloads returns 200, 222KB.
    # Old /FundsAndPerformance/Pages/FactSheet.aspx was 404.
    # ------------------------------------------------------------------
    {
        "issuer_name": "Nippon India Mutual Fund",
        "product_name": "Nippon India Investor Services Downloads",
        "product_category": "mutual_fund",
        "source_url": "https://mf.nipponindiaim.com/investor-services/downloads",
        "doc_format": "hub",
        "page_type": "amc_downloads_hub",
        "verified_status": 200,
        "notes": (
            "Nippon India investor services downloads hub — verified HTTP 200, 222KB HTML. "
            "Old /FundsAndPerformance/Pages/FactSheet.aspx was 404. "
            "Use Playwright to render JS and extract PDF links."
        ),
    },
    # ------------------------------------------------------------------
    # UTI Mutual Fund — hub page returns 200; PDFs are JS-rendered.
    # ------------------------------------------------------------------
    {
        "issuer_name": "UTI Mutual Fund",
        "product_name": "UTI MF Factsheets Hub",
        "product_category": "mutual_fund",
        "source_url": "https://www.utimf.com/downloads/factsheets",
        "doc_format": "hub",
        "page_type": "amc_factsheet_hub",
        "verified_status": 200,
        "notes": (
            "UTI MF factsheets hub — verified HTTP 200, 13KB HTML shell. "
            "PDF links are JS-rendered; Playwright/dynamic scraping required. "
            "Original direct PDF URL returned text/html (not a PDF) — excluded."
        ),
    },
    # ------------------------------------------------------------------
    # Health Insurance Benchmark Policies (Online Policy Sources)
    # ------------------------------------------------------------------
    {
        "issuer_name": "Care Health Insurance",
        "product_name": "Care Supreme",
        "product_category": "health_insurance",
        "source_url": "https://www.careinsurance.com/product/care-supreme",
        "doc_format": "html",
        "page_type": "policy_portal",
        "verified_status": 200,
        "notes": "Care Supreme portal page - 0% room rent sublimit, up to 500% cumulative bonus.",
    },
    {
        "issuer_name": "HDFC ERGO General Insurance",
        "product_name": "Optima Secure",
        "product_category": "health_insurance",
        "source_url": "https://www.hdfcergo.com/health-insurance/optima-secure",
        "doc_format": "html",
        "page_type": "policy_portal",
        "verified_status": 200,
        "notes": "HDFC ERGO Optima Secure portal page - 2X coverage from Day 1, no room rent cap.",
    },
    {
        "issuer_name": "Niva Bupa Health Insurance",
        "product_name": "ReAssure 2.0",
        "product_category": "health_insurance",
        "source_url": "https://www.nivabupa.com/health-insurance-plans/reassure-2-0.html",
        "doc_format": "html",
        "page_type": "policy_portal",
        "verified_status": 200,
        "notes": "Niva Bupa ReAssure 2.0 portal page - Lock the clock, unlimited re-instatement.",
    },
    {
        "issuer_name": "Star Health & Allied Insurance",
        "product_name": "Star Comprehensive Insurance Policy",
        "product_category": "health_insurance",
        "source_url": "https://www.starhealth.in/health-insurance-plans/star-comprehensive-insurance-policy",
        "doc_format": "html",
        "page_type": "policy_portal",
        "verified_status": 200,
        "notes": "Star Comprehensive policy portal page - Day care coverage, second medical opinion.",
    },
]
