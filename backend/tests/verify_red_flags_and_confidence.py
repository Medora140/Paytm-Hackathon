import os
import sys
import uuid
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_db
from app.ingestion.pipeline import get_ingestion_pipeline
from app.ml.service import ml_service
from app.ml.mock_data import get_chunks_for_document
from app.schemas import DocumentType

def main():
    fixture_path = r"C:\Users\Medora Gomes\Downloads\sample_policy_for_money_docs_decoded.pdf"
    assert os.path.exists(fixture_path), f"Fixture not found at {fixture_path}"

    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    doc_id = str(uuid.uuid4())
    print("\n====================================================================")
    print(f"=== VERIFICATION: Re-uploading Test Fixture Document ===")
    print(f"=== Document ID: {doc_id} ===")
    print(f"=== Fixture: sample_policy_for_money_docs_decoded.pdf ({len(file_bytes)} bytes) ===")
    print("====================================================================\n")

    pipeline = get_ingestion_pipeline()
    result = pipeline.process_document(
        doc_id=doc_id,
        user_id="00000000-0000-4000-8000-000000000001",
        filename="sample_policy_for_money_docs_decoded.pdf",
        document_type=DocumentType.HEALTH_INSURANCE,
        file_bytes=file_bytes
    )

    print(f"\n>>> INGESTION RESULT: status={result['status']} | chunks={result['chunks_count']} | pages={result['pages_count']}")

    # 1. Compare Supabase chunks vs get_chunks_for_document
    db = get_db()
    count_res = db.table("document_chunks").select("count", count="exact").eq("document_id", doc_id).execute()
    supabase_chunk_count = count_res.count
    resolved_chunks = get_chunks_for_document(doc_id)
    resolved_chunk_count = len(resolved_chunks)

    print("\n====================================================================")
    print("=== 1. CHUNK RESOLUTION CONSISTENCY VERIFICATION ===")
    print("====================================================================")
    print(f"Supabase document_chunks count : {supabase_chunk_count}")
    print(f"chunk_resolver resolved count  : {resolved_chunk_count}")
    assert supabase_chunk_count == resolved_chunk_count, (
        f"MISMATCH! Supabase has {supabase_chunk_count} chunks, but chunk_resolver returned {resolved_chunk_count}"
    )
    print(">>> PASS: document_chunks in Supabase and chunk_resolver report the EXACT SAME chunk count!")

    # 2. Verify Red Flags Deduplication and Count
    print("\n====================================================================")
    print("=== 2. RED FLAGS DEDUPLICATION & PLAUSIBILITY VERIFICATION ===")
    print("====================================================================")
    flags_resp = ml_service.get_red_flags(doc_id)
    total_flags = flags_resp.count
    print(f"Total Red Flags detected: {total_flags}")

    # Check for duplicates of (plain_explanation + source_text)
    seen_pairs = set()
    duplicate_pairs = []
    for idx, f in enumerate(flags_resp.red_flags, start=1):
        pair = (f.plain_explanation.strip(), f.source_text.strip())
        if pair in seen_pairs:
            duplicate_pairs.append((idx, f.clause_label, pair))
        seen_pairs.add(pair)
        print(f"\nFlag #{idx}: [{f.severity.upper()}] Clause: {f.clause_label} (Page {f.page_number})")
        print(f"  Explanation : {f.plain_explanation}")
        print(f"  Source Text : {f.source_text}")

    assert len(duplicate_pairs) == 0, f"DUPLICATES FOUND! {duplicate_pairs}"
    print("\n>>> PASS: No two red_flags rows have identical plain_explanation + source_text!")

    assert 1 <= total_flags <= 20, f"Flag count {total_flags} is out of plausible single-digit-to-teens range!"
    print(f">>> PASS: Total distinct red flags ({total_flags}) is in plausible range (not inflated to 32)!")

    # 3. Verify Confidence Score & Breakdown Reconciliation
    print("\n====================================================================")
    print("=== 3. CONFIDENCE SCORE & BREAKDOWN RECONCILIATION VERIFICATION ===")
    print("====================================================================")
    score_resp = ml_service.get_confidence_score(doc_id)
    print(f"Confidence Score: {score_resp.score}/100")
    print("\nScore Breakdown:")
    breakdown_sum = 0
    for b in score_resp.breakdown:
        breakdown_sum += b.points
        sign = "+" if b.points > 0 else ""
        print(f"  {sign}{b.points:>4} pts | {b.reason}")

    print(f"\nSum of Breakdown Items: {breakdown_sum}")
    print(f"Returned Final Score  : {score_resp.score}")
    assert score_resp.score > 0, f"Confidence score is stuck at 0! score={score_resp.score}"
    assert breakdown_sum == score_resp.score, (
        f"RECONCILIATION ERROR: Breakdown sum ({breakdown_sum}) does not equal score ({score_resp.score})!"
    )
    print(">>> PASS: Confidence score is non-zero (> 0) and breakdown sums exactly to returned score!")

    print("\n====================================================================")
    print("=== ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY! ===")
    print("====================================================================\n")

if __name__ == "__main__":
    main()
