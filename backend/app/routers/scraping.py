from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, status
from app.schemas import BenchmarkCompareResponse
from app.scraping.service import BenchmarkService

router = APIRouter(prefix="/documents/{id}", tags=["Benchmark & Scraping Service"])

# Singleton benchmark service instance
_benchmark_service = BenchmarkService()


@router.get("/compare", response_model=BenchmarkCompareResponse, status_code=status.HTTP_200_OK)
async def compare_document_with_market_benchmarks(
    id: str,
    category: Optional[str] = Query(None, description="Optional document category override (mutual_fund, health_insurance, loan)"),
    issuer_name: Optional[str] = Query(None, description="Optional issuer name override (e.g. HDFC Mutual Fund)")
) -> BenchmarkCompareResponse:
    """
    Get benchmark comparison table comparing this document's terms against cached
    scraped policy products in the same category from Supabase (populated via n8n scraping jobs).
    Wired to BenchmarkService with market comparables and robots.txt-compliant intelligence.
    """
    # Detect category and issuer from document metadata if not provided
    detected_category = category
    detected_issuer = issuer_name

    if not detected_category or not detected_issuer:
        from app.ingestion.repository import repository
        doc = repository.get_document(id)
        if doc:
            if not detected_category:
                dt = doc.get("document_type")
                detected_category = dt.value if hasattr(dt, "value") else str(dt)
            if not detected_issuer:
                detected_issuer = doc.get("issuer_name")

    if not detected_category:
        detected_category = "health_insurance"

    return _benchmark_service.get_comparisons_for_document(
        document_id=id,
        category=detected_category,
        issuer_name=detected_issuer
    )
