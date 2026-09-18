from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
try:
    from app.schemas import ScrapeJobStatus
except ImportError:
    from backend.app.schemas import ScrapeJobStatus


class ScrapedProduct(BaseModel):
    id: Optional[str] = None
    product_category: str = "mutual_fund"
    issuer_name: str
    product_name: str
    source_url: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    complaint_signal: Dict[str, Any] = Field(default_factory=dict)
    last_scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapeJobRecord(BaseModel):
    id: Optional[str] = None
    source_url: str
    status: ScrapeJobStatus
    triggered_by: str = "manual"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
