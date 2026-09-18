import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app.schemas import DocumentType
from app.ingestion.pipeline import get_ingestion_pipeline
from app.ingestion.repository import repository
from app.ml.service import ml_service
from app.db import get_db

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

print("=================================================================")
print("RUNNING LIVE END-TO-END DOCUMENT INGESTION & ML ANALYSIS PIPELINE")
print("=================================================================\n")

pipeline = get_ingestion_pipeline()
db = get_db()

# ---------------------------------------------------------------------
# Document 1: Mutual Fund Handbook
# ---------------------------------------------------------------------
mf_pdf_path = os.path.join(CURRENT_DIR, "tests", "HDFC MF Handbook (Aug 2024) (1)_0.pdf")
with open(mf_pdf_path, "rb") as f:
    mf_bytes = f.read()

print(f"1. Ingesting Mutual Fund Handbook ({len(mf_bytes)} bytes)...")
mf_result = pipeline.process_document(
    file_bytes=mf_bytes,
    filename="HDFC_MF_Handbook_Aug2024.pdf",
    document_type=DocumentType.MUTUAL_FUND
)
mf_doc_id = mf_result["document_id"]
print(f"   -> Created Document ID: {mf_doc_id}")
print(f"   -> Chunks extracted & saved in repository: {mf_result['chunks_count']}")

# Direct query check on Supabase
print("   -> Checking Supabase document_chunks directly...")
try:
    direct_q = db.table("document_chunks").select("*").eq("document_id", mf_doc_id).execute()
    data = direct_q.data if hasattr(direct_q, "data") else direct_q
    print(f"   -> Supabase direct query result: {len(data) if isinstance(data, list) else data}")
except Exception as e:
    print(f"   -> Supabase direct query exception: {type(e).__name__}: {e}")

# Call ML Service for Mutual Fund Summary & Red Flags
print("\n   -> Running ML Summary Generator (Live Gemini)...")
mf_summary = ml_service.get_summary(mf_doc_id)

print("\n   -> Running ML Red Flag Detector...")
mf_flags = ml_service.get_red_flags(mf_doc_id)


# ---------------------------------------------------------------------
# Document 2: Health Insurance Policy
# ---------------------------------------------------------------------
hi_pdf_path = os.path.join(CURRENT_DIR, "tests", "sample_health_insurance.pdf")
with open(hi_pdf_path, "rb") as f:
    hi_bytes = f.read()

print(f"\n2. Ingesting Health Insurance Policy ({len(hi_bytes)} bytes)...")
hi_result = pipeline.process_document(
    file_bytes=hi_bytes,
    filename="Star_Health_Premier_Policy.pdf",
    document_type=DocumentType.HEALTH_INSURANCE
)
hi_doc_id = hi_result["document_id"]
print(f"   -> Created Document ID: {hi_doc_id}")
print(f"   -> Chunks extracted & saved in repository: {hi_result['chunks_count']}")

# Direct query check on Supabase
print("   -> Checking Supabase document_chunks directly...")
try:
    direct_q2 = db.table("document_chunks").select("*").eq("document_id", hi_doc_id).execute()
    data2 = direct_q2.data if hasattr(direct_q2, "data") else direct_q2
    print(f"   -> Supabase direct query result: {len(data2) if isinstance(data2, list) else data2}")
except Exception as e:
    print(f"   -> Supabase direct query exception: {type(e).__name__}: {e}")

# Call ML Service for Health Insurance Summary & Red Flags
print("\n   -> Running ML Summary Generator (Live Gemini)...")
hi_summary = ml_service.get_summary(hi_doc_id)

print("\n   -> Running ML Red Flag Detector...")
hi_flags = ml_service.get_red_flags(hi_doc_id)


# ---------------------------------------------------------------------
# Output Verification & Reporting
# ---------------------------------------------------------------------
print("\n" + "=" * 70)
print("MUTUAL FUND DOCUMENT REPORT")
print("=" * 70)
print(f"Document ID: {mf_doc_id}")
print(f"Model Version: {mf_summary.model_version}")
print("\n[Coverage / Objectives]:")
for c in mf_summary.coverage:
    print(f"  * {c}")
print("\n[Exclusions / Restrictions]:")
for ex in mf_summary.exclusions:
    print(f"  * {ex}")
print("\n[Key Fees & Expenses]:")
for fee in mf_summary.key_fees:
    print(f"  * {fee}")
print("\n[Waiting Periods / Lock-in]:")
for wp in mf_summary.waiting_periods:
    print(f"  * {wp}")
print("\n[Notable Terms]:")
for nt in mf_summary.notable_terms:
    print(f"  * {nt}")

print(f"\n[Detected Red Flags] ({mf_flags.count} flags):")
for f in mf_flags.red_flags:
    print(f"  - [{f.severity.value.upper()}] Pattern: {f.pattern_id} | Page: {f.page_number}")
    print(f"    Clause: {f.clause_label}")
    print(f"    Explanation: {f.plain_explanation}")
    print(f"    Source Quote: {f.source_text[:120]}...\n")


print("=" * 70)
print("HEALTH INSURANCE DOCUMENT REPORT")
print("=" * 70)
print(f"Document ID: {hi_doc_id}")
print(f"Model Version: {hi_summary.model_version}")
print("\n[Coverage / Benefits]:")
for c in hi_summary.coverage:
    print(f"  * {c}")
print("\n[Exclusions]:")
for ex in hi_summary.exclusions:
    print(f"  * {ex}")
print("\n[Key Fees / Sub-limits / Co-pays]:")
for fee in hi_summary.key_fees:
    print(f"  * {fee}")
print("\n[Waiting Periods]:")
for wp in hi_summary.waiting_periods:
    print(f"  * {wp}")
print("\n[Notable Terms]:")
for nt in hi_summary.notable_terms:
    print(f"  * {nt}")

print(f"\n[Detected Red Flags] ({hi_flags.count} flags):")
for f in hi_flags.red_flags:
    print(f"  - [{f.severity.value.upper()}] Pattern: {f.pattern_id} | Page: {f.page_number}")
    print(f"    Clause: {f.clause_label}")
    print(f"    Explanation: {f.plain_explanation}")
    print(f"    Source Quote: {f.source_text[:120]}...\n")
