import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_user

def test_endpoints_return_clean_404_on_invalid_uuid():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "00000000-0000-4000-8000-000000000001",
        "email": "test@example.com"
    }
    client = TestClient(app)
    bad_ids = [
        "not-a-real-id",
        "doc_a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "doc_8f1b2c3d-4e5a-6b7c-8d9e-0f1a2b3c4d5e",
        "12345",
        "invalid_uuid_string",
    ]

    endpoints = [
        ("/documents/{id}", "GET"),
        ("/documents/{id}", "DELETE"),
        ("/documents/{id}/summary", "GET"),
        ("/documents/{id}/red-flags", "GET"),
        ("/documents/{id}/confidence-score", "GET"),
        ("/documents/{id}/chat", "POST"),
    ]

    print("\n====================================================================")
    print("=== BUG 2 VERIFICATION: Testing Endpoints with Non-UUID IDs ===")
    print("====================================================================")

    for bad_id in bad_ids:
        print(f"\n--- Testing invalid ID: '{bad_id}' ---")
        for path_template, method in endpoints:
            url = path_template.replace("{id}", bad_id)
            if method == "GET":
                res = client.get(url)
            elif method == "DELETE":
                res = client.delete(url)
            elif method == "POST":
                res = client.post(url, json={"question": "Is maternity covered?"})
            
            # None of these should EVER return 500
            print(f"[{method}] {url:<50} -> HTTP {res.status_code} | {res.json()}")
            assert res.status_code == 404, f"Expected HTTP 404 for {url}, got {res.status_code}: {res.text}"
            assert res.status_code != 500, f"Endpoint {url} returned 500 internal server error!"

    # Test seeded real sample document
    sample_id = "00000000-0000-4000-8000-000000000002"
    print(f"\n--- Testing Seeded Sample Document (Real UUID): '{sample_id}' ---")
    doc_res = client.get(f"/documents/{sample_id}")
    print(f"[GET] /documents/{sample_id:<39} -> HTTP {doc_res.status_code}")
    assert doc_res.status_code == 200, f"Failed to get seeded sample doc: {doc_res.text}"

    sum_res = client.get(f"/documents/{sample_id}/summary")
    print(f"[GET] /documents/{sample_id}/summary -> HTTP {sum_res.status_code} | clauses: {len(sum_res.json().get('clauses', []))}")
    assert sum_res.status_code == 200

    flags_res = client.get(f"/documents/{sample_id}/red-flags")
    print(f"[GET] /documents/{sample_id}/red-flags -> HTTP {flags_res.status_code} | count: {flags_res.json().get('count')}")
    assert flags_res.status_code == 200

    score_res = client.get(f"/documents/{sample_id}/confidence-score")
    print(f"[GET] /documents/{sample_id}/confidence-score -> HTTP {score_res.status_code} | score: {score_res.json().get('score')}/100")
    assert score_res.status_code == 200

    print("\n>>> BUG 2 VERIFICATION COMPLETED SUCCESSFULLY! All endpoints return clean 404s on bad IDs and 200 on sample document.")

if __name__ == "__main__":
    test_endpoints_return_clean_404_on_invalid_uuid()
