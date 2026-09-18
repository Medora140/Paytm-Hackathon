try:
    from app.scraping.repository import ScrapeRepository
    from app.scraping.service import BenchmarkService
    from app.scraping.models import ScrapedProduct, ScrapeJobRecord
except ImportError:
    from backend.app.scraping.repository import ScrapeRepository
    from backend.app.scraping.service import BenchmarkService
    from backend.app.scraping.models import ScrapedProduct, ScrapeJobRecord

__all__ = [
    "ScrapeRepository",
    "BenchmarkService",
    "ScrapedProduct",
    "ScrapeJobRecord",
]
