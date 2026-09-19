import os
import sys
import pytest

# Ensure backend root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.schemas import SeverityLevel
from app.ml.knowledge_base import RedFlagKnowledgeBase, STARTER_KNOWLEDGE_BASE
from app.ml.red_flag_detector import RuleBasedRedFlagDetector
from app.ml.confidence_score import calculate_confidence_score, SEVERITY_WEIGHTS
from app.ml.summary_generator import generate_plain_language_summary
from app.ml.rag_chat import GroundedRAGChat
from app.ml.mock_data import SYNTHETIC_MUTUAL_FUND_CHUNKS, get_chunks_for_document
from app.ml.service import MLService


# =====================================================================
# 1. Test Red-Flag Detection on Synthetic Mutual Fund Clauses
# =====================================================================

def test_starter_kb_contains_mutual_fund_patterns():
    kb = RedFlagKnowledgeBase()
    patterns = kb.get_patterns(category="mutual_fund")
    clause_types = {p.clause_type for p in patterns}
    
    assert "exit_load" in clause_types, "Knowledge Base must contain exit_load pattern"
    assert "expense_ratio" in clause_types, "Knowledge Base must contain expense_ratio pattern"


def test_red_flag_detection_on_synthetic_mutual_fund_clauses():
    """
    Verify that rule-based detector finds the expected clause types in a synthetic mutual fund clause set:
    specifically exit_load, expense_ratio, and lock-in period clauses.
    """
    detector = RuleBasedRedFlagDetector()
    results = detector.detect_red_flags("test_mf_doc_01", SYNTHETIC_MUTUAL_FUND_CHUNKS)
    
    detected_types = {flag.pattern_id for flag in results}
    assert len(results) >= 2, f"Expected at least 2 red flags, found {len(results)}"
    
    # Check that both exit_load and expense_ratio were detected
    has_exit_load = any("exit_load" in flag.pattern_id for flag in results)
    has_expense_ratio = any("expense_ratio" in flag.pattern_id for flag in results)
    
    assert has_exit_load, f"Expected exit_load to be detected among: {detected_types}"
    assert has_expense_ratio, f"Expected expense_ratio to be detected among: {detected_types}"

    # Verify that each detected flag has valid citations and metadata
    for flag in results:
        assert flag.document_id == "test_mf_doc_01"
        assert flag.page_number > 0
        assert flag.chunk_id is not None
        assert len(flag.source_text) > 0
        assert flag.plain_explanation is not None
        assert flag.severity in [SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]


# =====================================================================
# 2. Test Confidence Score Formula & Bounds (§3)
# =====================================================================

def test_confidence_score_formula_and_breakdown_math():
    """
    Verify that confidence score formula:
    score = 100 - sum(severity_weights) - benchmark_penalty + transparency_bonus
    clamped to [0, 100], and breakdown items sum to the expected total.
    """
    detector = RuleBasedRedFlagDetector()
    flags = detector.detect_red_flags("test_mf_doc_01", SYNTHETIC_MUTUAL_FUND_CHUNKS)
    
    result = calculate_confidence_score("test_mf_doc_01", flags, benchmark_penalty=5, transparency_bonus=2)
    
    assert 0 <= result.score <= 100, f"Score {result.score} must be bounded in [0, 100]"
    
    # Calculate expected deductions from flags
    expected_flag_deductions = sum(SEVERITY_WEIGHTS[flag.severity] for flag in flags)
    raw_expected_score = 100 - expected_flag_deductions - 5 + 2
    clamped_expected_score = max(0, min(100, raw_expected_score))
    
    assert result.score == clamped_expected_score
    
    # Verify breakdown items sum correctly
    breakdown_total = sum(item.points for item in result.breakdown)
    # The breakdown sum equals the unclamped score
    assert breakdown_total == raw_expected_score


def test_confidence_score_edge_cases_bounded_0_to_100():
    """
    Test extreme cases:
    - Many severe red flags (must clamp to 0, never negative)
    - Zero flags with big bonus (must clamp to 100, never exceed 100)
    """
    # Create extreme penalty flags
    class MockFlag:
        def __init__(self, severity, clause_label):
            self.severity = severity
            self.clause_label = clause_label
    
    heavy_flags = [MockFlag(SeverityLevel.HIGH, f"Extreme Risk {i}") for i in range(10)]  # 10 * 15 = 150 pts penalty
    res_zero = calculate_confidence_score("doc_heavy", heavy_flags, benchmark_penalty=30)
    assert res_zero.score == 0, f"Score should clamp at 0, got {res_zero.score}"
    
    # No flags + high bonus
    res_max = calculate_confidence_score("doc_clean", [], transparency_bonus=15)
    assert res_max.score == 100, f"Score should clamp at 100, got {res_max.score}"


# =====================================================================
# 3. Test RAG Chat Refuses Outside Information
# =====================================================================

def test_rag_chat_refuses_outside_queries():
    """
    Verify that RAG chat strictly refuses to answer questions outside the provided chunks,
    returning a refusal response without hallucinating.
    """
    chat_engine = GroundedRAGChat()
    
    outside_questions = [
        "What is the capital of Australia?",
        "What is the current stock price of Apple Inc.?",
        "How do I cook pasta carbonara?",
        "Can you prescribe antibiotics for a fever?"
    ]
    
    for q in outside_questions:
        response = chat_engine.chat("test_mf_doc_01", q, SYNTHETIC_MUTUAL_FUND_CHUNKS)
        content_lower = response.content.lower()
        
        # Must indicate refusal or not found in document
        is_refusal = (
            "not found" in content_lower or
            "not mentioned" in content_lower or
            "not covered" in content_lower or
            "cannot answer" in content_lower or
            "only answer questions related" in content_lower or
            "outside" in content_lower or
            "does not contain" in content_lower
        )
        assert is_refusal, f"Expected refusal for outside query '{q}', got: '{response.content}'"
        # Refusals should cite no chunks or mark empty citations
        assert len(response.citations) == 0, f"Expected 0 citations for out-of-scope query, got: {response.citations}"


def test_rag_chat_answers_grounded_queries():
    """
    Verify that RAG chat answers questions that ARE present in the chunks,
    returning relevant citations.
    """
    chat_engine = GroundedRAGChat()
    
    question = "What is the exit load if I redeem units within 365 days?"
    response = chat_engine.chat("test_mf_doc_01", question, SYNTHETIC_MUTUAL_FUND_CHUNKS)
    
    content_lower = response.content.lower()
    assert ("1%" in content_lower or "exit load" in content_lower or "365" in content_lower)
    assert len(response.citations) > 0, "Grounded answer must have citations"
    assert response.citations[0].chunk_id is not None
    assert response.citations[0].page_number > 0


# =====================================================================
# 4. Test Summary Generation
# =====================================================================

def test_summary_generation_schema():
    """
    Verify structured summary generation returns valid schema fields
    (coverage, exclusions, key_fees, waiting_periods, notable_terms).
    """
    summary = generate_plain_language_summary(
        document_id="test_mf_doc_01",
        chunks=SYNTHETIC_MUTUAL_FUND_CHUNKS,
        language="en",
        document_type="mutual_fund"
    )
    
    assert summary.document_id == "test_mf_doc_01"
    assert summary.language == "en"
    assert isinstance(summary.coverage, list)
    assert isinstance(summary.exclusions, list)
    assert isinstance(summary.key_fees, list)
    assert isinstance(summary.waiting_periods, list)
    assert isinstance(summary.notable_terms, list)
    assert len(summary.key_fees) > 0 or len(summary.coverage) > 0


# =====================================================================
# 5. Validation on Real Mutual Fund Handbook Fixture
# =====================================================================

def test_real_mutual_fund_handbook_fixture():
    """
    Re-validate red flag detector against the real mutual fund handbook
    fixture at backend/tests/HDFC MF Handbook (Aug 2024) (1)_0.pdf.
    """
    pdf_path = os.path.join(CURRENT_DIR, "HDFC MF Handbook (Aug 2024) (1)_0.pdf")
    assert os.path.exists(pdf_path), f"Fixture PDF not found at {pdf_path}"
    
    # Extract text from the first 25 pages of the real handbook
    import fitz
    doc = fitz.open(pdf_path)
    assert len(doc) > 0, "PDF should have pages"
    
    chunks = []
    # Sample up to 30 pages to test realistic scale
    max_pages = min(30, len(doc))
    for page_idx in range(max_pages):
        page = doc[page_idx]
        text = page.get_text("text").strip()
        if text:
            chunks.append({
                "id": f"chk_real_p{page_idx+1}",
                "page_number": page_idx + 1,
                "clause_label": f"Page {page_idx+1} Content",
                "text": text
            })
    doc.close()
    
    assert len(chunks) > 0, "Extracted chunks should not be empty"
    
    detector = RuleBasedRedFlagDetector()
    flags = detector.detect_red_flags("real_hdfc_mf_doc", chunks)
    
    # The real handbook contains discussions of exit loads, expense ratios, and lock-in
    assert len(flags) > 0, "Red flag detector should flag relevant clauses in the real mutual fund handbook"
    
    # Calculate score
    score_res = calculate_confidence_score("real_hdfc_mf_doc", flags)
    assert 0 <= score_res.score <= 100


# =====================================================================
# 6. Test Wired API Endpoints
# =====================================================================

def test_wired_api_endpoints():
    """
    Verify the endpoints wired in app.routers.ml:
    - GET /documents/{id}/summary
    - GET /documents/{id}/red-flags
    - GET /documents/{id}/confidence-score
    - POST /documents/{id}/chat
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.auth import get_current_user
    from app.schemas import DocumentType
    from app.ingestion.repository import repository
    from app.ml.mock_data import SYNTHETIC_MUTUAL_FUND_CHUNKS

    user_id = "00000000-0000-4000-8000-000000000001"
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "email": "test@moneydocs.internal",
    }

    client = TestClient(app)
    doc_id = "00000000-0000-4000-8000-000000000099"
    repository.create_document(
        doc_id=doc_id,
        user_id=user_id,
        filename="test_mf.pdf",
        document_type=DocumentType.MUTUAL_FUND,
        storage_path=f"test/{doc_id}.pdf"
    )
    repository.save_chunks(doc_id, SYNTHETIC_MUTUAL_FUND_CHUNKS)

    try:
        # Summary
        sum_resp = client.get(f"/documents/{doc_id}/summary")
        assert sum_resp.status_code == 200
        sum_data = sum_resp.json()
        assert sum_data["document_id"] == doc_id
        assert "coverage" in sum_data
        assert "exclusions" in sum_data
        assert "key_fees" in sum_data

        # Red flags
        rf_resp = client.get(f"/documents/{doc_id}/red-flags")
        assert rf_resp.status_code == 200
        rf_data = rf_resp.json()
        assert rf_data["document_id"] == doc_id
        assert rf_data["count"] >= 2
        assert len(rf_data["red_flags"]) >= 2

        # Confidence score
        cs_resp = client.get(f"/documents/{doc_id}/confidence-score")
        assert cs_resp.status_code == 200
        cs_data = cs_resp.json()
        assert cs_data["document_id"] == doc_id
        assert 0 <= cs_data["score"] <= 100
        assert len(cs_data["breakdown"]) > 0

        # Chat grounded
        chat_resp = client.post(f"/documents/{doc_id}/chat", json={"question": "What is the exit load?"})
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert chat_data["document_id"] == doc_id
        assert len(chat_data["citations"]) > 0

        # Chat out of scope refusal
        refusal_resp = client.post(f"/documents/{doc_id}/chat", json={"question": "What is the capital of Australia?"})
        assert refusal_resp.status_code == 200
        refusal_data = refusal_resp.json()
        assert "not found" in refusal_data["content"].lower()
        assert len(refusal_data["citations"]) == 0
    finally:
        app.dependency_overrides.clear()

