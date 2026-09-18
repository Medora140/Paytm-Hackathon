import sys
import os
import io
# import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.schemas import (
    SessionResponse,
    DocumentUploadResponse,
    DocumentDetailResponse,
    DocumentDeleteResponse,
    DocumentSummaryResponse,
    RedFlagsResponse,
    ConfidenceScoreResponse,
    ChatResponse,
    BenchmarkCompareResponse,
    WebhookAckResponse
)

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_auth_session():
    res = client.post("/auth/session", json={"access_token": "mock-jwt-token"})
    assert res.status_code == 200
    parsed = SessionResponse(**res.json())
    assert parsed.email == "demo.user@moneydocs.dev"
    assert parsed.is_active is True


UPLOADED_DOC_ID = "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"


def test_upload_document():
    global UPLOADED_DOC_ID
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test Health Insurance Policy. Clause 4.2 Room rent 1%.")
    pdf_bytes = doc.tobytes()
    doc.close()

    res = client.post(
        "/documents",
        files={"file": ("test_policy.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "health_insurance"}
    )
    assert res.status_code == 201
    parsed = DocumentUploadResponse(**res.json())
    assert parsed.status == "uploaded"
    assert parsed.filename == "test_policy.pdf"
    UPLOADED_DOC_ID = parsed.id


def test_list_documents():
    res = client.get("/documents")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1
    assert docs[0]["document_type"] == "health_insurance"


def test_get_document():
    doc_id = UPLOADED_DOC_ID
    res = client.get(f"/documents/{doc_id}")
    assert res.status_code == 200
    parsed = DocumentDetailResponse(**res.json())
    assert parsed.id == doc_id
    assert parsed.status in ["uploaded", "analyzed", "chunked", "embedded"]


def test_delete_document():
    doc_id = UPLOADED_DOC_ID
    res = client.delete(f"/documents/{doc_id}")
    assert res.status_code == 200
    parsed = DocumentDeleteResponse(**res.json())
    assert parsed.status == "deleted"
    assert "DPDP" in parsed.message


def test_document_summary():
    doc_id = "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
    res = client.get(f"/documents/{doc_id}/summary")
    assert res.status_code == 200
    parsed = DocumentSummaryResponse(**res.json())
    assert len(parsed.coverage) > 0
    assert len(parsed.exclusions) > 0
    assert len(parsed.key_fees) > 0
    assert len(parsed.waiting_periods) > 0


def test_document_red_flags():
    doc_id = "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
    res = client.get(f"/documents/{doc_id}/red-flags")
    assert res.status_code == 200
    parsed = RedFlagsResponse(**res.json())
    assert parsed.count == len(parsed.red_flags)
    assert parsed.count > 0
    first_flag = parsed.red_flags[0]
    assert first_flag.page_number > 0
    assert first_flag.severity in ["high", "medium", "low"]


def test_document_confidence_score():
    doc_id = "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
    res = client.get(f"/documents/{doc_id}/confidence-score")
    assert res.status_code == 200
    parsed = ConfidenceScoreResponse(**res.json())
    assert 0 <= parsed.score <= 100
    assert len(parsed.breakdown) > 0


def test_document_chat():
    doc_id = "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
    res = client.post(f"/documents/{doc_id}/chat", json={"question": "What is the room rent limit?"})
    assert res.status_code == 200
    parsed = ChatResponse(**res.json())
    assert parsed.role == "assistant"
    assert len(parsed.citations) > 0


def test_document_compare():
    doc_id = "doc_8f1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"
    res = client.get(f"/documents/{doc_id}/compare")
    assert res.status_code == 200
    parsed = BenchmarkCompareResponse(**res.json())
    assert len(parsed.comparables) > 0
    assert len(parsed.comparables[0].attributes) > 0


def test_webhook_scrape_complete():
    payload = {
        "job_id": "job_12345",
        "source_url": "https://example.com/care-policy",
        "status": "success",
        "items_scraped": 15,
        "finished_at": "2026-09-18T10:00:00Z"
    }
    res = client.post("/webhooks/n8n/scrape-complete", json=payload)
    assert res.status_code == 200
    parsed = WebhookAckResponse(**res.json())
    assert parsed.success is True


def test_webhook_kb_updated():
    payload = {
        "kb_version": "kb_v2026.09_irda_ombudsman",
        "patterns_added": 5,
        "timestamp": "2026-09-18T10:00:00Z"
    }
    res = client.post("/webhooks/n8n/kb-updated", json=payload)
    assert res.status_code == 200
    parsed = WebhookAckResponse(**res.json())
    assert parsed.success is True


if __name__ == "__main__":
    test_health()
    test_auth_session()
    test_upload_document()
    test_list_documents()
    test_get_document()
    test_delete_document()
    test_document_summary()
    test_document_red_flags()
    test_document_confidence_score()
    test_document_chat()
    test_document_compare()
    test_webhook_scrape_complete()
    test_webhook_kb_updated()
    print("ALL 13 API STUB ENDPOINT TESTS PASSED SUCCESSFULLY!")
