import json
import logging
import os
import sys
from io import StringIO

# Add backend directory to sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.ml.gemini_client import (
    probe_gemini_connectivity,
    get_gemini_client,
    reset_gemini_cache,
)
from app.ml.summary_generator import generate_plain_language_summary
from app.ml.rag_chat import GroundedRAGChat
from app.ml.mock_data import SYNTHETIC_MUTUAL_FUND_CHUNKS, MOCK_HEALTH_INSURANCE_CHUNKS
from app.ml.red_flag_detector import RuleBasedRedFlagDetector
from app.ml.confidence_score import calculate_confidence_score

# Set up logging capture for verification
log_capture_stream = StringIO()
handler = logging.StreamHandler(log_capture_stream)
formatter = logging.Formatter("[%(levelname)s] [%(name)s] %(message)s")
handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)


def run_all_verifications():
    print("=======================================================================")
    print("TRACK 2: GEMINI CONNECTIVITY & FALLBACK CLEANUP — AUDIT VERIFICATION")
    print("=======================================================================\n")

    # -------------------------------------------------------------------------
    # Verification 1: Direct SDK probe verification with GEMINI_API_KEY
    # -------------------------------------------------------------------------
    print(">>> 1. Testing Direct Live Connectivity Probe (SDK)...")
    reset_gemini_cache()
    is_connected, error_msg, client = probe_gemini_connectivity(force_refresh=True)
    assert is_connected is True, f"Expected live Gemini probe to succeed, got error: {error_msg}"
    assert client is not None, "Client should be initialized"
    print("    [PASS] Probe succeeded. Live Gemini connection verified.")
    print(f"    [INFO] Client: {type(client).__name__}")

    # Verify cache works
    cached_client = get_gemini_client()
    assert cached_client is client, "get_gemini_client() must return the cached verified instance"
    print("    [PASS] Caching verified: Subsequent call reused cached client without re-probing.")

    # -------------------------------------------------------------------------
    # Verification 2: Zero format-based key validation check
    # -------------------------------------------------------------------------
    print("\n>>> 2. Testing Key Validation: No prefix restrictions, loud fallback on empty key...")
    # Test with empty key
    is_conn_empty, err_empty, _ = probe_gemini_connectivity(api_key="", force_refresh=True)
    assert is_conn_empty is False, "Empty key must return is_connected=False"
    assert "missing" in err_empty.lower(), f"Expected missing key error, got: {err_empty}"
    print("    [PASS] Empty key correctly triggers fallback.")

    # Restore real key probe
    reset_gemini_cache()
    is_connected, _, client = probe_gemini_connectivity(force_refresh=True)
    assert is_connected is True

    # -------------------------------------------------------------------------
    # Verification 3: Loud fallback warnings across ML modules
    # -------------------------------------------------------------------------
    print("\n>>> 3. Testing Loud Visible Fallback Warnings...")
    # Trigger fallback in red flag detector with empty chunks
    detector = RuleBasedRedFlagDetector()
    flags = detector.detect_red_flags("empty_doc", chunks=[])
    assert flags == [], "Empty chunks must return empty list"
    
    captured_logs = log_capture_stream.getvalue()
    assert "[FALLBACK WARNING] [red_flag_detector]" in captured_logs, "Expected loud fallback warning in red_flag_detector"
    print("    [PASS] red_flag_detector loud fallback warning confirmed.")

    # -------------------------------------------------------------------------
    # Verification 4: End-to-End Live Document Summaries with distinct outputs
    # -------------------------------------------------------------------------
    print("\n>>> 4. Testing End-to-End Live Gemini Summaries on 2 Different Documents...")

    # Document 1: Mutual Fund Document
    print("    Calling generate_plain_language_summary for Mutual Fund document...")
    log_capture_stream.truncate(0)
    log_capture_stream.seek(0)
    
    mf_summary = generate_plain_language_summary(
        document_id="doc_mf_live_001",
        chunks=SYNTHETIC_MUTUAL_FUND_CHUNKS,
        language="en",
        document_type="mutual_fund"
    )

    mf_logs = log_capture_stream.getvalue()
    assert "[LIVE GEMINI CALL] [summary_generator]" in mf_logs, "Missing live Gemini call log line for MF"
    assert "[LIVE GEMINI SUCCESS] [summary_generator]" in mf_logs, "Missing live Gemini success log line for MF"
    assert mf_summary.model_version.startswith("gemini-"), f"Expected gemini model, got {mf_summary.model_version}"
    print(f"    [PASS] Mutual Fund summary generated via live Gemini API ({mf_summary.model_version}).")

    # Document 2: Health Insurance Document
    print("    Calling generate_plain_language_summary for Health Insurance document...")
    log_capture_stream.truncate(0)
    log_capture_stream.seek(0)

    hi_summary = generate_plain_language_summary(
        document_id="doc_hi_live_002",
        chunks=MOCK_HEALTH_INSURANCE_CHUNKS,
        language="en",
        document_type="health_insurance"
    )

    hi_logs = log_capture_stream.getvalue()
    assert "[LIVE GEMINI CALL] [summary_generator]" in hi_logs, "Missing live Gemini call log line for HI"
    assert "[LIVE GEMINI SUCCESS] [summary_generator]" in hi_logs, "Missing live Gemini success log line for HI"
    assert hi_summary.model_version.startswith("gemini-"), f"Expected gemini model, got {hi_summary.model_version}"
    print(f"    [PASS] Health Insurance summary generated via live Gemini API ({hi_summary.model_version}).")

    # Verify that summaries are genuinely different and tuned to their document types
    print("\n>>> Checking content divergence between Mutual Fund and Health Insurance summaries:")
    mf_text = " ".join(mf_summary.coverage + mf_summary.exclusions + mf_summary.key_fees).lower()
    hi_text = " ".join(hi_summary.coverage + hi_summary.exclusions + hi_summary.key_fees).lower()

    print(f"    - MF Summary Sample: {mf_summary.coverage[0]}")
    print(f"    - HI Summary Sample: {hi_summary.coverage[0]}")

    assert mf_summary.coverage != hi_summary.coverage, "Summaries must be different"
    assert ("equity" in mf_text or "fund" in mf_text or "large-cap" in mf_text or "nav" in mf_text), (
        "Mutual Fund summary must reflect mutual fund domain terms"
    )
    assert ("hospital" in hi_text or "room" in hi_text or "pre-existing" in hi_text or "insurance" in hi_text or "rent" in hi_text), (
        "Health Insurance summary must reflect health insurance domain terms"
    )
    print("    [PASS] Summaries are genuinely different and accurately reflect the respective input documents!")

    # -------------------------------------------------------------------------
    # Verification 5: Live Grounded RAG Chat Call
    # -------------------------------------------------------------------------
    print("\n>>> 5. Testing Live Grounded RAG Chat...")
    log_capture_stream.truncate(0)
    log_capture_stream.seek(0)

    rag = GroundedRAGChat()
    chat_resp = rag.chat(
        document_id="doc_mf_live_001",
        question="What is the exit load if I redeem within 365 days?",
        chunks=SYNTHETIC_MUTUAL_FUND_CHUNKS,
        language="en"
    )

    chat_logs = log_capture_stream.getvalue()
    assert "[LIVE GEMINI CALL] [rag_chat]" in chat_logs, "Missing live Gemini call log line in RAG chat"
    assert "[LIVE GEMINI SUCCESS] [rag_chat]" in chat_logs, "Missing live Gemini success log line in RAG chat"
    print(f"    [PASS] Live RAG Chat answer received: '{chat_resp.content[:90]}...'")
    print(f"    [INFO] Cited chunks: {chat_resp.cited_chunk_ids}")

    print("\n=======================================================================")
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO FAILURES!")
    print("=======================================================================")


if __name__ == "__main__":
    run_all_verifications()
