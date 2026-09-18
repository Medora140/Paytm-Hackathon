import os
import sys
import time
import subprocess
import httpx

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
SCRAPER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scraper"))
PYTHON_EXE = os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe")

print("================================================================")
print("       RUNNING MONEY DOCS DECODED END-TO-END VERIFICATION       ")
print("================================================================")

# 1. Start FastAPI Backend Server
print("\n[STEP 1] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
backend_proc = subprocess.Popen(
    [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=BACKEND_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# 2. Start Next.js Frontend Server
print("[STEP 2] Starting Next.js Production Server on http://127.0.0.1:3000 ...")
frontend_proc = subprocess.Popen(
    ["npm.cmd", "run", "start", "--", "-p", "3000"],
    cwd=FRONTEND_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

def cleanup():
    print("\nShutting down background servers...")
    try:
        bout, berr = backend_proc.communicate(timeout=3)
        print("\n--- BACKEND STDOUT ---")
        print(bout)
        print("--- BACKEND STDERR ---")
        print(berr)
    except Exception:
        backend_proc.kill()
    try:
        frontend_proc.terminate()
        frontend_proc.wait(timeout=3)
    except Exception:
        frontend_proc.kill()

try:
    # Wait for servers to become ready
    print("Waiting for servers to become ready...")
    backend_ready = False
    frontend_ready = False
    
    for i in range(30):
        if not backend_ready:
            try:
                r = httpx.get("http://127.0.0.1:8000/health", timeout=1.0)
                if r.status_code == 200:
                    backend_ready = True
                    print(f" -> Backend ready! Status: {r.json()}")
            except Exception:
                pass
        
        if not frontend_ready:
            try:
                r = httpx.get("http://127.0.0.1:3000", timeout=1.0)
                if r.status_code == 200:
                    frontend_ready = True
                    print(" -> Frontend ready! HTTP 200 OK")
            except Exception:
                pass
        
        if backend_ready and frontend_ready:
            break
        time.sleep(1)

    if not backend_ready:
        raise RuntimeError("FastAPI Backend failed to become ready.")
    if not frontend_ready:
        raise RuntimeError("Next.js Frontend failed to become ready.")

    print("\n[STEP 3] Testing Backend API Endpoints directly...")
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

    # Health
    r = client.get("/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print(" [PASS] GET /health - OK")

    # Auth
    r = client.post("/auth/session", json={"access_token": "mock-token"})
    assert r.status_code == 200 and r.json()["is_active"] is True
    print(" [PASS] POST /auth/session - OK")

    # Generate valid sample PDF for ingestion pipeline
    import fitz
    sample_doc = fitz.open()
    p = sample_doc.new_page()
    p.insert_text((50, 50), "Standard Health Insurance Policy. Clause 4.2 Room rent is capped at 1% per day.")
    pdf_bytes = sample_doc.tobytes()
    sample_doc.close()

    # Upload document
    files = {"file": ("test_policy.pdf", pdf_bytes, "application/pdf")}
    data = {"document_type": "health_insurance"}
    r = client.post("/documents", files=files, data=data)
    assert r.status_code == 201
    doc_id = r.json()["id"]
    print(f" [PASS] POST /documents - OK (Created {doc_id})")

    # List documents
    r = client.get("/documents")
    assert r.status_code == 200 and len(r.json()) >= 1
    print(f" [PASS] GET /documents - OK ({len(r.json())} documents returned)")

    # Get document detail
    r = client.get(f"/documents/{doc_id}")
    assert r.status_code == 200 and r.json()["status"] in ["uploaded", "analyzed", "embedded", "chunked"]
    print(f" [PASS] GET /documents/{doc_id} - OK (Status: {r.json()['status']})")

    # Summary
    r = client.get(f"/documents/{doc_id}/summary")
    assert r.status_code == 200 and len(r.json()["coverage"]) > 0
    print(f" [PASS] GET /documents/{doc_id}/summary - OK ({len(r.json()['coverage'])} coverage clauses)")

    # Red flags
    r = client.get(f"/documents/{doc_id}/red-flags")
    assert r.status_code == 200 and r.json()["count"] > 0
    print(f" [PASS] GET /documents/{doc_id}/red-flags - OK ({r.json()['count']} red flags identified)")

    # Confidence score
    r = client.get(f"/documents/{doc_id}/confidence-score")
    assert r.status_code == 200 and 0 <= r.json()["score"] <= 100
    print(f" [PASS] GET /documents/{doc_id}/confidence-score - OK (Score: {r.json()['score']}/100)")

    # Chat
    r = client.post(f"/documents/{doc_id}/chat", json={"question": "What is the room rent limit?"})
    assert r.status_code == 200 and len(r.json()["citations"]) > 0
    print(f" [PASS] POST /documents/{doc_id}/chat - OK (Grounded with {len(r.json()['citations'])} citations)")

    # Compare
    r = client.get(f"/documents/{doc_id}/compare")
    assert r.status_code == 200 and len(r.json()["comparables"]) > 0
    print(f" [PASS] GET /documents/{doc_id}/compare - OK ({len(r.json()['comparables'])} market comparables)")

    # Webhook scrape complete
    r = client.post("/webhooks/n8n/scrape-complete", json={
        "job_id": "job_e2e_test",
        "source_url": "https://careinsurance.com",
        "status": "success",
        "items_scraped": 8,
        "finished_at": "2026-09-18T11:00:00Z"
    })
    assert r.status_code == 200 and r.json()["success"] is True
    print(" [PASS] POST /webhooks/n8n/scrape-complete - OK")

    # Webhook KB updated
    r = client.post("/webhooks/n8n/kb-updated", json={
        "kb_version": "kb_v2026.09_e2e",
        "patterns_added": 3,
        "timestamp": "2026-09-18T11:00:00Z"
    })
    assert r.status_code == 200 and r.json()["success"] is True
    print(" [PASS] POST /webhooks/n8n/kb-updated - OK")

    # Delete document (DPDP erasure)
    r = client.delete(f"/documents/{doc_id}")
    assert r.status_code == 200 and r.json()["status"] == "deleted"
    print(f" [PASS] DELETE /documents/{doc_id} - OK (DPDP right to erasure)")

    print("\n[STEP 4] Testing Frontend Pages with live backend integration...")
    f_client = httpx.Client(base_url="http://127.0.0.1:3000", timeout=5.0)

    pages_to_test = [
        ("/", "Landing page"),
        ("/upload", "Document Upload page"),
        (f"/doc/{doc_id}", "Document Dashboard"),
        (f"/doc/{doc_id}/chat", "Conversational Q&A chat"),
        (f"/doc/{doc_id}/compare", "Benchmark comparison table"),
        ("/documents", "Document history"),
        ("/settings", "User settings"),
        ("/admin", "Admin health monitor")
    ]

    for path, description in pages_to_test:
        resp = f_client.get(path)
        assert resp.status_code == 200, f"Page {path} returned status {resp.status_code}"
        print(f" [PASS] {description} ({path}) -> HTTP 200 OK")

    print("\n[STEP 5] Testing Scraper Service Stub...")
    scraper_res = subprocess.run(
        [PYTHON_EXE, os.path.join(SCRAPER_DIR, "main.py"), "--help"],
        capture_output=True,
        text=True
    )
    assert scraper_res.returncode == 0, f"Scraper error: {scraper_res.stderr}"
    assert "Money Docs Decoded Scraper Worker" in scraper_res.stdout
    print(" [PASS] Scraper worker execution -> SUCCESS (CLI --help OK)")

    print("\n================================================================")
    print("   ALL END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!      ")
    print("================================================================")

finally:
    cleanup()
