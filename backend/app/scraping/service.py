from datetime import datetime
from typing import Optional

from app.schemas import BenchmarkCompareResponse, BenchmarkProductItem
from app.scraping.repository import ScrapeRepository


class BenchmarkService:
    """Returns only benchmark data actually collected by the scraper."""

    def __init__(self, repository: Optional[ScrapeRepository] = None):
        self.repo = repository or ScrapeRepository()

    def get_comparisons_for_document(self, document_id: str, category: str = "mutual_fund", issuer_name: Optional[str] = None) -> BenchmarkCompareResponse:
        records = self.repo.get_benchmark_products(category=category, issuer_name=issuer_name)
        comparables = [
            BenchmarkProductItem(
                id=str(row["id"]), product_category=row.get("product_category", category),
                issuer_name=row.get("issuer_name", "Unknown issuer"), product_name=row.get("product_name", "Unnamed product"),
                source_url=row.get("source_url", ""), attributes=row.get("attributes", {}),
                complaint_signal=row.get("complaint_signal", {}), last_scraped_at=row.get("last_scraped_at") or datetime.utcnow(),
            )
            for row in records
        ]
        return BenchmarkCompareResponse(
            document_id=document_id, product_category=category, issuer_name=issuer_name,
            comparables=comparables, last_scraped_at=comparables[0].last_scraped_at if comparables else None,
            data_freshness_label="No scraped benchmark data is available yet." if not comparables else "Scraped benchmark data.",
        )
