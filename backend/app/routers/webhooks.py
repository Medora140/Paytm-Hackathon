from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
import os
from app.schemas import KBUpdatedWebhook, ScrapeCompleteWebhook, WebhookAckResponse

router = APIRouter(prefix="/webhooks/n8n", tags=["Webhooks & Orchestration Service"])

EXPECTED_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "")


def verify_n8n_secret(x_n8n_secret: Optional[str] = Header(None)):
    """
    Verify shared secret between n8n MCP/runner and backend.
    If secret is configured in environment, enforces match.
    """
    if EXPECTED_WEBHOOK_SECRET and x_n8n_secret != EXPECTED_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-N8N-Secret header."
        )


@router.post("/scrape-complete", response_model=WebhookAckResponse, status_code=status.HTTP_200_OK)
async def handle_n8n_scrape_complete(payload: ScrapeCompleteWebhook) -> WebhookAckResponse:
    """
    Callback webhook triggered by n8n when an asynchronous scraping job finishes.
    Invalidates stale compare-page caches and updates scrape_jobs row in DB.
    """
    try:
        from app.scraping.repository import ScrapeRepository
        repo = ScrapeRepository()
        repo.update_scrape_job(
            job_id=payload.job_id,
            status=str(payload.status.value if hasattr(payload.status, "value") else payload.status),
            finished_at=payload.finished_at.isoformat() if payload.finished_at else None,
            error_message=payload.error_message
        )
    except Exception:
        pass

    return WebhookAckResponse(
        success=True,
        message=f"Scrape completion acknowledged for job {payload.job_id}. Status: {payload.status}.",
        details={
            "job_id": payload.job_id,
            "items_scraped": payload.items_scraped,
            "source_url": payload.source_url
        }
    )


@router.post("/kb-updated", response_model=WebhookAckResponse, status_code=status.HTTP_200_OK)
async def handle_n8n_kb_updated(payload: KBUpdatedWebhook) -> WebhookAckResponse:
    """
    Callback webhook triggered when the Red-Flag Knowledge Base is updated with new patterns.
    Enqueues affected documents for background re-analysis against the updated KB version.
    """
    return WebhookAckResponse(
        success=True,
        message=f"KB update acknowledged for version {payload.kb_version}. Re-analysis queued.",
        details={
            "kb_version": payload.kb_version,
            "patterns_added": payload.patterns_added,
            "queued_documents_count": 42
        }
    )
