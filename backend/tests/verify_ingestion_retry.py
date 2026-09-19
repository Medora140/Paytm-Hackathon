import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_user
from app.db import get_db
from app.ingestion.pipeline import get_ingestion_pipeline
from app.identity import DEMO_USER_ID, DEMO_USER_EMAIL

def run_verification():
    print("=== Starting Ingestion Re-submission & Retry Verification ===")
    app.dependency_overrides[get_current_user] = lambda: {"id": DEMO_USER_ID, "email": DEMO_USER_EMAIL}
    client = TestClient(app)
    db = get_db()
    pipeline = get_ingestion_pipeline()

    # Read sample PDF
    pdf_path = os.path.join(os.path.dirname(__file__), "sample_health_insurance.pdf")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    headers = {"Authorization": "Bearer test-token"}

    # Step 1: Upload a fresh document
    fresh_doc_id = str(uuid.uuid4())
    print(f"\n[1] Uploading fresh document with ID: {fresh_doc_id}")
    files = {"file": ("star_health_policy.pdf", pdf_bytes, "application/pdf")}
    data = {"document_type": "health_insurance", "doc_id": fresh_doc_id}

    resp1 = client.post("/documents", headers=headers, files=files, data=data)
    print(f"Initial Upload Response: status={resp1.status_code}, data={resp1.json()}")
    assert resp1.status_code == 201, f"Expected 201, got {resp1.status_code}: {resp1.text}"
    returned_id = resp1.json()["id"]
    assert returned_id == fresh_doc_id, f"Expected {fresh_doc_id}, got {returned_id}"

    # Execute pipeline processing
    print(f"\n[2] Executing pipeline for document: {fresh_doc_id}")
    process_res1 = pipeline.process_document(
        file_bytes=pdf_bytes,
        filename="star_health_policy.pdf",
        document_type="health_insurance",
        user_id=DEMO_USER_ID,
        doc_id=fresh_doc_id
    )
    print(f"Pipeline Execution 1 result: {process_res1}")
    assert process_res1["status"].value == "analyzed"
    assert process_res1["chunks_count"] > 0

    # Step 2: Deliberately re-trigger upload with the SAME document ID (simulating retry / reload re-submission)
    print(f"\n[3] Deliberately re-submitting with the SAME document ID (retry simulation): {fresh_doc_id}")
    files_retry = {"file": ("star_health_policy.pdf", pdf_bytes, "application/pdf")}
    data_retry = {"document_type": "health_insurance", "doc_id": fresh_doc_id}

    resp2 = client.post("/documents", headers=headers, files=files_retry, data=data_retry)
    print(f"Re-submission Response: status={resp2.status_code}, data={resp2.json()}")
    assert resp2.status_code == 201, f"Expected 201 (no 409 Conflict), got {resp2.status_code}: {resp2.text}"

    # Step 3: Call pipeline.process_document again on the same ID (verify idempotency)
    print(f"\n[4] Re-calling pipeline.process_document on existing analyzed ID (idempotency check)...")
    process_res2 = pipeline.process_document(
        file_bytes=pdf_bytes,
        filename="star_health_policy.pdf",
        document_type="health_insurance",
        user_id=DEMO_USER_ID,
        doc_id=fresh_doc_id
    )
    print(f"Pipeline Execution 2 (idempotent) result: {process_res2}")
    assert process_res2["status"].value == "analyzed"
    assert process_res2["chunks_count"] == process_res1["chunks_count"]

    # Step 5: Verify downstream endpoints return 200 OK and populate persisted records
    print(f"\n[5] Verifying downstream API endpoints for doc '{fresh_doc_id}':")
    summary_endpoint = client.get(f"/documents/{fresh_doc_id}/summary", headers=headers)
    print(f" - /summary: status={summary_endpoint.status_code}")
    assert summary_endpoint.status_code == 200, f"Expected 200, got {summary_endpoint.status_code}: {summary_endpoint.text}"

    red_flags_endpoint = client.get(f"/documents/{fresh_doc_id}/red-flags", headers=headers)
    print(f" - /red-flags: status={red_flags_endpoint.status_code}")
    assert red_flags_endpoint.status_code == 200, f"Expected 200, got {red_flags_endpoint.status_code}: {red_flags_endpoint.text}"

    score_endpoint = client.get(f"/documents/{fresh_doc_id}/confidence-score", headers=headers)
    print(f" - /confidence-score: status={score_endpoint.status_code}")
    assert score_endpoint.status_code == 200, f"Expected 200, got {score_endpoint.status_code}: {score_endpoint.text}"

    chat_endpoint = client.post(
        f"/documents/{fresh_doc_id}/chat",
        headers=headers,
        json={"question": "What is the room rent cap in this policy?"}
    )
    print(f" - /chat: status={chat_endpoint.status_code}")
    assert chat_endpoint.status_code == 200, f"Expected 200, got {chat_endpoint.status_code}: {chat_endpoint.text}"

    # Step 6: Direct Supabase database queries
    print(f"\n[6] Direct Supabase Query Verification for doc '{fresh_doc_id}':")
    chunks_query = db.table("document_chunks").select("count", count="exact").eq("document_id", fresh_doc_id).execute()
    print(f" - document_chunks count: {chunks_query.count}")
    assert chunks_query.count > 0, "No chunks found in Supabase document_chunks!"

    summaries_query = db.table("document_summaries").select("*").eq("document_id", fresh_doc_id).execute()
    print(f" - document_summaries rows: {len(summaries_query.data)}")
    assert len(summaries_query.data) > 0, "No summary found in Supabase document_summaries!"

    flags_query = db.table("red_flags").select("*").eq("document_id", fresh_doc_id).execute()
    print(f" - red_flags rows: {len(flags_query.data)}")
    assert len(flags_query.data) > 0, "No red flags found in Supabase red_flags!"

    scores_query = db.table("confidence_scores").select("*").eq("document_id", fresh_doc_id).execute()
    print(f" - confidence_scores rows: {len(scores_query.data)}")
    assert len(scores_query.data) > 0, "No confidence score found in Supabase confidence_scores!"

    chat_query = db.table("chat_messages").select("*").eq("document_id", fresh_doc_id).execute()
    print(f" - chat_messages rows: {len(chat_query.data)}")
    assert len(chat_query.data) > 0, "No chat messages found in Supabase chat_messages!"

    print("\n=== ALL VERIFICATION CHECKS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_verification()
