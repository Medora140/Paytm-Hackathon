import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

try:
    from app.db import get_db, db_helper
    from app.runtime_flags import allow_in_memory_stores
except ImportError:
    try:
        from backend.app.db import get_db, db_helper
        from backend.app.runtime_flags import allow_in_memory_stores
    except ImportError:
        get_db = None
        db_helper = None
        def allow_in_memory_stores(): return False

logger = logging.getLogger("ScrapeRepository")


class ScrapeRepository:
    """
    Database access layer for benchmark_products and scrape_jobs.
    Live environment directly targets Supabase PostgreSQL tables.
    In-memory storage is restricted to explicit test execution.
    """

    def __init__(self, in_memory: bool = False):
        client = get_db() if get_db else None
        is_stub = client is None or client.__class__.__name__ == "StubSupabaseClient"
        self.in_memory = in_memory or (allow_in_memory_stores() and (not (db_helper and db_helper.is_configured) or is_stub))
        self._memory_benchmark_products: List[Dict[str, Any]] = []
        self._memory_scrape_jobs: List[Dict[str, Any]] = []

    def save_benchmark_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update benchmark product."""
        record = dict(product)
        if not record.get("id"):
            record["id"] = f"bp_{uuid.uuid4().hex[:12]}"
        if not record.get("last_scraped_at"):
            record["last_scraped_at"] = datetime.utcnow().isoformat()

        if self.in_memory:
            # Upsert into in-memory list
            for i, existing in enumerate(self._memory_benchmark_products):
                if (existing.get("product_category") == record.get("product_category") and
                    existing.get("issuer_name") == record.get("issuer_name") and
                    existing.get("product_name") == record.get("product_name")):
                    self._memory_benchmark_products[i] = record
                    return record
            self._memory_benchmark_products.append(record)
            return record

        try:
            client = get_db()
            response = client.table("benchmark_products").upsert(record).execute()
            if response and hasattr(response, "data") and response.data:
                return response.data[0]
            return record
        except Exception as e:
            logger.warning(f"Supabase upsert failed, falling back to memory: {e}")
            self._memory_benchmark_products.append(record)
            return record

    def get_benchmark_products(
        self,
        category: str,
        issuer_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve benchmark products by category and optional issuer."""
        if self.in_memory:
            matched = [
                p for p in self._memory_benchmark_products
                if p.get("product_category", "").lower() == category.lower()
            ]
            if issuer_name:
                issuer_matched = [
                    p for p in matched
                    if issuer_name.lower() in p.get("issuer_name", "").lower() or
                       p.get("issuer_name", "").lower() in issuer_name.lower()
                ]
                if issuer_matched:
                    return issuer_matched
            return matched

        try:
            client = get_db()
            query = client.table("benchmark_products").select("*").eq("product_category", category)
            if issuer_name:
                query = query.ilike("issuer_name", f"%{issuer_name}%")
            result = query.execute()
            if result and hasattr(result, "data") and result.data:
                return result.data
            # If empty and issuer_name was specified, fallback to category search
            if issuer_name:
                fallback_result = client.table("benchmark_products").select("*").eq("product_category", category).execute()
                if fallback_result and hasattr(fallback_result, "data"):
                    return fallback_result.data
            return []
        except Exception as e:
            logger.warning(f"Failed to query Supabase benchmark_products: {e}")
            return [
                p for p in self._memory_benchmark_products
                if p.get("product_category", "").lower() == category.lower()
            ]

    def create_scrape_job(
        self,
        source_url: str,
        triggered_by: str = "manual",
        status: str = "pending"
    ) -> str:
        """Create a new scrape_job record and return its ID."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        job_record = {
            "id": job_id,
            "source_url": source_url,
            "status": status,
            "triggered_by": triggered_by,
            "started_at": now,
            "finished_at": None,
            "error_message": None
        }

        if self.in_memory:
            self._memory_scrape_jobs.append(job_record)
            return job_id

        try:
            client = get_db()
            client.table("scrape_jobs").insert(job_record).execute()
        except Exception as e:
            logger.warning(f"Supabase insert scrape_jobs failed, storing in memory: {e}")
            self._memory_scrape_jobs.append(job_record)

        return job_id

    def update_scrape_job(
        self,
        job_id: str,
        status: str,
        finished_at: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update scrape_jobs row with finish status and optional error message."""
        finish_time = finished_at or datetime.utcnow().isoformat()
        update_data = {
            "status": status,
            "finished_at": finish_time,
            "error_message": error_message
        }

        if self.in_memory:
            for job in self._memory_scrape_jobs:
                if job["id"] == job_id:
                    job.update(update_data)
                    return
            return

        try:
            client = get_db()
            client.table("scrape_jobs").update(update_data).eq("id", job_id).execute()
        except Exception as e:
            logger.warning(f"Supabase update scrape_jobs failed: {e}")
            for job in self._memory_scrape_jobs:
                if job["id"] == job_id:
                    job.update(update_data)

    def get_scrape_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve recent scrape jobs."""
        if self.in_memory:
            return list(self._memory_scrape_jobs)

        try:
            client = get_db()
            result = client.table("scrape_jobs").select("*").order("started_at", desc=True).limit(50).execute()
            if result and hasattr(result, "data") and result.data:
                return result.data
            return list(self._memory_scrape_jobs)
        except Exception as e:
            logger.warning(f"Supabase get_scrape_jobs failed: {e}")
            return list(self._memory_scrape_jobs)
