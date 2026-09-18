import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project directories to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
SCRAPER_DIR = os.path.join(PROJECT_ROOT, "scraper")

for path in (PROJECT_ROOT, BASE_DIR, SCRAPER_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from scraper.robots_guard import RobotsGuard
from scraper.extractor import extract_mutual_fund_facts, normalize_to_benchmark_product
from scraper.seed_urls import SEED_BENCHMARK_SOURCES
from scraper.main import run_batch_scrape, ScrapeJobResult
from backend.app.schemas import BenchmarkProductItem, BenchmarkCompareResponse
from backend.app.scraping.repository import ScrapeRepository
from backend.app.scraping.service import BenchmarkService


class TestRobotsGuard(unittest.TestCase):
    """Test robots.txt compliance and guard rules."""

    def setUp(self):
        self.guard = RobotsGuard(user_agent="MoneyDocsDecodedBot/1.0")

    def test_robots_allowed(self):
        robots_content = """
User-agent: *
Disallow: /private/
Disallow: /admin/
Allow: /downloads/
"""
        with patch.object(self.guard, "_fetch_robots_txt", return_value=robots_content):
            allowed = self.guard.can_fetch("https://www.hdfcfund.com/downloads/factsheet.pdf")
            self.assertTrue(allowed, "URL under /downloads/ should be allowed by robots.txt")

    def test_robots_disallowed(self):
        robots_content = """
User-agent: *
Disallow: /private/
Disallow: /restricted-factsheets/
"""
        with patch.object(self.guard, "_fetch_robots_txt", return_value=robots_content):
            allowed = self.guard.can_fetch("https://www.hdfcfund.com/restricted-factsheets/secret.pdf")
            self.assertFalse(allowed, "URL under /restricted-factsheets/ should be disallowed by robots.txt")


class TestExtractorAndNormalization(unittest.TestCase):
    """Test data extraction from documents and normalization into benchmark_products schema."""

    def test_extracted_attributes_normalization(self):
        sample_text = """
HDFC Top 100 Fund - Large Cap Fund
Investment Objective: To provide long-term capital appreciation.
Benchmark Index: NIFTY 100 TRI
Fund Manager: Rahul Baijal
AUM: Rs 34,250.45 Crores as of August 31, 2024
Total Expense Ratio (TER):
Regular Plan: 1.62% p.a.
Direct Plan: 0.98% p.a.
Exit Load: In respect of each purchase / switch-in of units, 1.00% is payable if units are redeemed / switched-out within 1 year from the date of allotment. Nil thereafter.
Portfolio Turnover Ratio: 24.50%
Riskometer: Very High Risk
"""
        extracted = extract_mutual_fund_facts(
            text=sample_text,
            issuer_name="HDFC Mutual Fund",
            product_name="HDFC Top 100 Fund",
            source_url="https://www.hdfcfund.com/factsheet/hdfc-top-100.pdf"
        )

        normalized = normalize_to_benchmark_product(extracted)

        # Validate schema adherence
        self.assertEqual(normalized["product_category"], "mutual_fund")
        self.assertEqual(normalized["issuer_name"], "HDFC Mutual Fund")
        self.assertEqual(normalized["product_name"], "HDFC Top 100 Fund")
        self.assertIn("expense_ratio_regular", normalized["attributes"])
        self.assertIn("expense_ratio_direct", normalized["attributes"])
        self.assertIn("exit_load", normalized["attributes"])
        self.assertIn("benchmark_index", normalized["attributes"])
        self.assertIn("fund_manager", normalized["attributes"])
        self.assertIn("aum_crores", normalized["attributes"])
        self.assertIn("riskometer", normalized["attributes"])

        # Validate complaint signal
        self.assertIn("source", normalized["complaint_signal"])
        self.assertIn("complaints_resolved_percent", normalized["complaint_signal"])

        # Validate against Pydantic schema
        product_item = BenchmarkProductItem(
            id=normalized["id"],
            product_category=normalized["product_category"],
            issuer_name=normalized["issuer_name"],
            product_name=normalized["product_name"],
            source_url=normalized["source_url"],
            attributes=normalized["attributes"],
            complaint_signal=normalized["complaint_signal"],
            last_scraped_at=datetime.fromisoformat(normalized["last_scraped_at"])
        )
        self.assertEqual(product_item.product_category, "mutual_fund")

    def test_extraction_against_local_pdf_fixture(self):
        fixture_path = os.path.join(BASE_DIR, "tests", "HDFC MF Handbook (Aug 2024) (1)_0.pdf")
        self.assertTrue(os.path.exists(fixture_path), f"Test fixture not found: {fixture_path}")

        with open(fixture_path, "rb") as f:
            pdf_bytes = f.read()

        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        extracted_pages = []
        for i in range(min(5, len(doc))):
            extracted_pages.append(doc[i].get_text("text"))
        doc.close()

        combined_text = "\n".join(extracted_pages)
        self.assertTrue(len(combined_text) > 100, "Should extract text from HDFC handbook fixture")

        facts = extract_mutual_fund_facts(
            text=combined_text,
            issuer_name="HDFC Mutual Fund",
            product_name="HDFC Mutual Fund Handbook Schemes",
            source_url="local://tests/HDFC_MF_Handbook_Aug_2024.pdf"
        )
        normalized = normalize_to_benchmark_product(facts)
        self.assertEqual(normalized["issuer_name"], "HDFC Mutual Fund")
        self.assertEqual(normalized["product_category"], "mutual_fund")
        self.assertTrue(isinstance(normalized["attributes"], dict))


class TestBatchScraperResilience(unittest.TestCase):
    """Test batch scraper execution, robots.txt skipping, and graceful per-source failure."""

    def setUp(self):
        self.repo = ScrapeRepository(in_memory=True)

    def test_robots_disallowed_source_is_skipped_and_logged(self):
        test_seeds = [
            {
                "issuer_name": "Disallowed Fund House",
                "product_name": "Disallowed Equity Fund",
                "product_category": "mutual_fund",
                "source_url": "https://www.disallowed-fund.example.com/schemes/factsheet.pdf"
            }
        ]

        with patch("scraper.main.RobotsGuard.can_fetch", return_value=False), \
             patch("scraper.main.fetch_document_content") as mock_fetch:

            results = run_batch_scrape(seeds=test_seeds, repository=self.repo, triggered_by="test_suite")

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, "skipped_robots")
            self.assertIn("robots.txt", results[0].error_message.lower())
            mock_fetch.assert_not_called()

            # Verify scrape_jobs record
            jobs = self.repo.get_scrape_jobs()
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["status"], "skipped_robots")
            self.assertEqual(jobs[0]["source_url"], test_seeds[0]["source_url"])

    def test_failed_source_does_not_crash_batch(self):
        test_seeds = [
            {
                "issuer_name": "Failing AMC",
                "product_name": "Broken Scheme",
                "product_category": "mutual_fund",
                "source_url": "https://www.broken-fund.example.com/broken.pdf"
            },
            {
                "issuer_name": "Healthy AMC",
                "product_name": "Healthy Scheme",
                "product_category": "mutual_fund",
                "source_url": "https://www.healthy-fund.example.com/healthy.pdf"
            }
        ]

        def mock_fetch(url):
            if "broken" in url:
                raise ConnectionError("500 Internal Server Error / DNS failure")
            return b"%PDF-1.4 dummy pdf content for healthy scheme"

        with patch("scraper.main.RobotsGuard.can_fetch", return_value=True), \
             patch("scraper.main.fetch_document_content", side_effect=mock_fetch), \
             patch("scraper.main.extract_facts_from_content") as mock_extract:

            mock_extract.return_value = {
                "id": "bp_test_healthy",
                "product_category": "mutual_fund",
                "issuer_name": "Healthy AMC",
                "product_name": "Healthy Scheme",
                "source_url": "https://www.healthy-fund.example.com/healthy.pdf",
                "attributes": {"expense_ratio_regular": "1.45%", "expense_ratio_direct": "0.85%"},
                "complaint_signal": {"source": "SEBI SCORES 2024", "complaints_resolved_percent": 99.1},
                "last_scraped_at": datetime.utcnow().isoformat()
            }

            results = run_batch_scrape(seeds=test_seeds, repository=self.repo, triggered_by="test_resilience")

            self.assertEqual(len(results), 2, "Both jobs must be tracked")
            self.assertEqual(results[0].status, "failed")
            self.assertIn("500 Internal Server Error", results[0].error_message)
            self.assertEqual(results[1].status, "success")

            jobs = self.repo.get_scrape_jobs()
            self.assertEqual(len(jobs), 2)
            statuses = [j["status"] for j in jobs]
            self.assertIn("failed", statuses)
            self.assertIn("success", statuses)

            # Check benchmark products table has the healthy one
            products = self.repo.get_benchmark_products(category="mutual_fund")
            self.assertEqual(len(products), 1)
            self.assertEqual(products[0]["issuer_name"], "Healthy AMC")


class TestCompareEndpointWiring(unittest.TestCase):
    """Test wiring of BenchmarkService and the /documents/{id}/compare endpoint."""

    def setUp(self):
        self.repo = ScrapeRepository(in_memory=True)
        self.service = BenchmarkService(repository=self.repo)

        # Pre-seed benchmark products
        self.repo.save_benchmark_product({
            "id": "bp_seed_hdfc_flexi",
            "product_category": "mutual_fund",
            "issuer_name": "HDFC Mutual Fund",
            "product_name": "HDFC Flexi Cap Fund",
            "source_url": "https://www.hdfcfund.com/schemes/hdfc-flexi-cap",
            "attributes": {
                "expense_ratio_regular": "1.52%",
                "expense_ratio_direct": "0.88%",
                "exit_load": "1% within 1 year, Nil thereafter",
                "benchmark_index": "NIFTY 500 TRI",
                "fund_manager": "Roshi Jain",
                "aum_crores": "54,230.12",
                "riskometer": "Very High"
            },
            "complaint_signal": {
                "source": "AMFI Disclosures 2024",
                "complaints_resolved_percent": 99.4
            },
            "last_scraped_at": datetime.utcnow().isoformat()
        })

    def test_benchmark_service_exact_issuer_match(self):
        compare_data = self.service.get_comparisons_for_document(
            document_id="doc_123",
            category="mutual_fund",
            issuer_name="HDFC Mutual Fund"
        )
        self.assertEqual(compare_data.document_id, "doc_123")
        self.assertEqual(compare_data.product_category, "mutual_fund")
        self.assertEqual(compare_data.issuer_name, "HDFC Mutual Fund")
        self.assertGreaterEqual(len(compare_data.comparables), 1)
        self.assertEqual(compare_data.comparables[0].product_name, "HDFC Flexi Cap Fund")

    def test_benchmark_service_category_fallback(self):
        # When issuer is unknown, returns general market comparison for category
        compare_data = self.service.get_comparisons_for_document(
            document_id="doc_456",
            category="mutual_fund",
            issuer_name="Unknown New AMC"
        )
        self.assertEqual(compare_data.document_id, "doc_456")
        self.assertEqual(compare_data.product_category, "mutual_fund")
        self.assertGreaterEqual(len(compare_data.comparables), 1)
        self.assertIn("General market comparison", compare_data.data_freshness_label)

    def test_fastapi_compare_endpoint_route(self):
        from starlette.testclient import TestClient
        from backend.app.main import app

        client = TestClient(app)
        response = client.get("/documents/doc_test_mf_123/compare?category=mutual_fund&issuer_name=HDFC%20Mutual%20Fund")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["document_id"], "doc_test_mf_123")
        self.assertEqual(data["product_category"], "mutual_fund")
        self.assertIn("comparables", data)
        self.assertTrue(len(data["comparables"]) > 0)
        self.assertIn("target_attributes", data)


if __name__ == "__main__":
    unittest.main()

