import os
import io
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from app.main import app
from app.schemas import DocumentStatus, DocumentType
from app.ingestion.detector import PDFTypeDetector
from app.ingestion.extractor import PDFTextExtractor
from app.ingestion.chunker import ClauseChunker
from app.ingestion.embedder import ChunkEmbedder
from app.ingestion.storage import StorageManager
from app.ingestion.repository import DocumentRepository, repository
from app.ingestion.pipeline import IngestionPipeline


@pytest.fixture
def sample_handbook_path():
    # Check both backend/tests and backend/test
    p1 = os.path.join(BASE_DIR, "tests", "HDFC MF Handbook (Aug 2024) (1)_0.pdf")
    p2 = os.path.join(BASE_DIR, "test", "HDFC MF Handbook (Aug 2024) (1)_0.pdf")
    if os.path.exists(p1):
        return p1
    elif os.path.exists(p2):
        return p2
    else:
        pytest.skip(f"Handbook PDF not found at {p1} or {p2}")


@pytest.fixture
def synthetic_native_pdf():
    """Generates a pure text-native multi-page PDF in-memory using PyMuPDF."""
    import fitz
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 72), "MUTUAL FUND SCHEME INFORMATION DOCUMENT\nSection 1: Investment Objective\nThe scheme aims to generate long-term capital appreciation.")
    
    # Page 2
    p2 = doc.new_page()
    p2.insert_text((50, 72), "Section 2: Asset Allocation\nClause 2.1: Equity instruments: 65% to 100%.\nClause 2.2: Debt securities: 0% to 35%.\nClause 2.3: Exit Load\n1% if redeemed within 365 days.")
    
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


@pytest.fixture
def synthetic_scanned_pdf():
    """Generates a scanned PDF (image only, no text layer) in-memory."""
    import fitz
    doc = fitz.open()
    
    # Create an image with text rendered into pixels
    img = Image.new("RGB", (600, 300), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((30, 50), "SCANNED PAGE CLAUSE 4.1: EXIT LOAD 2 PERCENT", fill="black")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()
    
    page = doc.new_page(width=600, height=300)
    page.insert_image(page.rect, stream=img_bytes)
    
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def test_text_native_pdf_extraction(synthetic_native_pdf):
    """
    Test 1: Detects text-native PDF and extracts text page-by-page with page tagging.
    """
    detector = PDFTypeDetector()
    is_native, page_diagnostics = detector.inspect_pdf(synthetic_native_pdf)
    assert is_native is True
    assert len(page_diagnostics) == 2
    assert page_diagnostics[0]["is_scanned"] is False
    assert page_diagnostics[1]["is_scanned"] is False

    extractor = PDFTextExtractor()
    pages_data = extractor.extract(synthetic_native_pdf)
    assert len(pages_data) == 2
    assert pages_data[0]["page_number"] == 1
    assert "Investment Objective" in pages_data[0]["text"]
    assert pages_data[1]["page_number"] == 2
    assert "Asset Allocation" in pages_data[1]["text"]


def test_ocr_fallback_on_scanned_page(synthetic_scanned_pdf):
    """
    Test 2: Detects scanned page with no native text layer and triggers OCR fallback.
    """
    detector = PDFTypeDetector()
    is_native, page_diagnostics = detector.inspect_pdf(synthetic_scanned_pdf)
    assert page_diagnostics[0]["is_scanned"] is True

    extractor = PDFTextExtractor()
    # Mock OCR engine to return deterministic text verifying the fallback hook
    with patch.object(extractor, "_run_ocr_on_page", return_value="SCANNED PAGE CLAUSE 4.1: EXIT LOAD 2 PERCENT") as mock_ocr:
        pages_data = extractor.extract(synthetic_scanned_pdf)
        assert mock_ocr.called
        assert len(pages_data) == 1
        assert pages_data[0]["page_number"] == 1
        assert "EXIT LOAD 2 PERCENT" in pages_data[0]["text"]
        assert pages_data[0].get("is_ocr") is True


def test_clause_level_chunking_producing_page_tagged_chunks():
    """
    Test 3: Splits document text into semantically coherent clause-level chunks
    preserving page_number and generating clause_label.
    """
    pages_data = [
        {
            "page_number": 1,
            "text": (
                "SCHEME DETAILS\n"
                "Section 1. Scheme Highlights\n"
                "This is an open ended growth scheme.\n"
                "Clause 1.1 Benchmark Index\n"
                "The benchmark is NIFTY 50 TRI."
            )
        },
        {
            "page_number": 2,
            "text": (
                "Section 2. Risk Factors\n"
                "Mutual fund investments are subject to market risks.\n"
                "Clause 2.1 Liquidity Risk\n"
                "Redemption might be temporarily delayed under extreme market events.\n"
                "Clause 2.2 Exit Load\n"
                "An exit load of 1.00% is payable if units are redeemed within 1 year."
            )
        }
    ]

    chunker = ClauseChunker()
    chunks = chunker.chunk_pages(pages_data)

    assert len(chunks) >= 4
    # All chunks must have page_number, clause_label, text
    for chunk in chunks:
        assert "page_number" in chunk
        assert chunk["page_number"] in [1, 2]
        assert "clause_label" in chunk
        assert chunk["clause_label"] is not None
        assert "text" in chunk
        assert len(chunk["text"].strip()) > 0

    # Verify specific clauses were segmented by header
    labels = [c["clause_label"] for c in chunks]
    assert any("Highlights" in l or "1.1" in l for l in labels)
    assert any("Risk Factors" in l or "2.1" in l or "2.2" in l or "Exit Load" in l for l in labels)

    # Check page tagging correctness
    p2_chunks = [c for c in chunks if c["page_number"] == 2]
    assert len(p2_chunks) >= 2
    assert any("Exit Load" in c["text"] for c in p2_chunks)


def test_embedding_storage():
    """
    Test 4: Generates 384-dimensional embeddings and writes chunks to storage repository.
    """
    repo = DocumentRepository()
    embedder = ChunkEmbedder()

    doc_id = "test-doc-uuid-001"
    repo.create_document(
        doc_id=doc_id,
        user_id="usr-test-123",
        filename="test_mutual_fund.pdf",
        document_type=DocumentType.MUTUAL_FUND,
        storage_path=f"documents/{doc_id}/test_mutual_fund.pdf"
    )

    raw_chunks = [
        {
            "page_number": 1,
            "clause_label": "Section 1: Investment Objective",
            "text": "The scheme seeks to generate long term capital appreciation from an actively managed portfolio."
        },
        {
            "page_number": 2,
            "clause_label": "Clause 2.2: Exit Load",
            "text": "Exit load of 1% is charged if redeemed before 365 days from date of allotment."
        }
    ]

    embedded_chunks = embedder.embed_chunks(raw_chunks)
    assert len(embedded_chunks) == 2

    for c in embedded_chunks:
        assert "embedding" in c
        assert isinstance(c["embedding"], list)
        assert len(c["embedding"]) == 384  # vector(384) dimension

    repo.save_chunks(doc_id, embedded_chunks)
    repo.update_status(doc_id, DocumentStatus.EMBEDDED, pipeline_stage="Embedding complete")

    stored_chunks = repo.get_chunks(doc_id)
    assert len(stored_chunks) == 2
    assert stored_chunks[0]["page_number"] == 1
    assert stored_chunks[1]["page_number"] == 2
    assert len(stored_chunks[0]["embedding"]) == 384

    doc_meta = repo.get_document(doc_id)
    assert doc_meta["status"] == DocumentStatus.EMBEDDED


def test_pipeline_e2e_mutual_fund_handbook(sample_handbook_path):
    """
    Test 5: Runs the complete ingestion pipeline end-to-end against the HDFC MF Handbook PDF.
    Asserts a non-empty, page-tagged chunk set and verified document status.
    """
    with open(sample_handbook_path, "rb") as f:
        pdf_bytes = f.read()

        pipeline = IngestionPipeline()
        result = pipeline.process_document(
            file_bytes=pdf_bytes,
            filename=os.path.basename(sample_handbook_path),
            document_type=DocumentType.MUTUAL_FUND,
            user_id="00000000-0000-4000-8000-000000000001"
        )

        assert result["status"] in (DocumentStatus.EMBEDDED, DocumentStatus.ANALYZED)
    assert result["document_id"] is not None
    assert result["chunks_count"] > 0

    # Retrieve chunks from repository
    chunks = pipeline.repository.get_chunks(result["document_id"])
    assert len(chunks) > 0

    # Every chunk must be page-tagged with a valid page number
    page_numbers = set()
    for chunk in chunks:
        assert "page_number" in chunk
        assert chunk["page_number"] >= 1
        page_numbers.add(chunk["page_number"])
        assert "text" in chunk and len(chunk["text"].strip()) > 0
        assert "embedding" in chunk
        assert len(chunk["embedding"]) == 384

    # Multiple pages should have been extracted and tagged
    assert len(page_numbers) > 1
    print(f"\n[E2E TEST SUCCESS] Processed {len(chunks)} page-tagged chunks across {len(page_numbers)} pages.")


def test_api_endpoints_wired_with_ingestion(synthetic_native_pdf):
    """
    Test 6: Tests API router endpoints (POST /documents, GET /documents/{id}, GET /documents, DELETE /documents/{id}).
    Verifies full integration without breaking schema contracts.
    """
    from app.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "00000000-0000-4000-8000-000000000001",
        "email": "test@moneydocs.internal",
    }
    client = TestClient(app)

    try:
        # 1. Upload via POST /documents
        files = {
            "file": ("test_policy.pdf", synthetic_native_pdf, "application/pdf")
        }
        data = {
            "document_type": DocumentType.MUTUAL_FUND.value
        }
        post_res = client.post("/documents", files=files, data=data)
        assert post_res.status_code == 201
        upload_data = post_res.json()
        assert "id" in upload_data
        assert upload_data["filename"] == "test_policy.pdf"
        assert upload_data["document_type"] == DocumentType.MUTUAL_FUND.value
        assert upload_data["status"] == DocumentStatus.UPLOADED.value
        doc_id = upload_data["id"]

        # 2. Query metadata & live status via GET /documents/{id}
        get_res = client.get(f"/documents/{doc_id}")
        assert get_res.status_code == 200
        detail_data = get_res.json()
        assert detail_data["id"] == doc_id
        assert detail_data["filename"] == "test_policy.pdf"
        assert detail_data["document_type"] == DocumentType.MUTUAL_FUND.value
        assert "pipeline_stage" in detail_data

        # 3. List documents via GET /documents
        list_res = client.get("/documents")
        assert list_res.status_code == 200
        items = list_res.json()
        assert isinstance(items, list)
        assert any(item["id"] == doc_id for item in items)

        # 4. 404 on nonexistent document
        nonexistent_res = client.get("/documents/non-existent-uuid")
        assert nonexistent_res.status_code == 404

        # 5. Delete document via DELETE /documents/{id} (DPDP erasure)
        del_res = client.delete(f"/documents/{doc_id}")
        assert del_res.status_code == 200
        del_data = del_res.json()
        assert del_data["status"] == "deleted"
        assert del_data["document_id"] == doc_id
    finally:
        app.dependency_overrides.clear()
