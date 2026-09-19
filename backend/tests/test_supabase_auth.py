import os
import sys
import uuid
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from app.main import app
from app.db import get_db

client = TestClient(app)


def test_supabase_auth_full_lifecycle():
    """
    REAL SUPABASE AUTH TEST SUITE:
    1. Successful user signup via real Supabase Auth
    2. Successful login with correct credentials
    3. Incorrect password rejection (HTTP 401)
    4. Missing authentication token rejection (HTTP 401)
    5. Invalid/malformed token rejection (HTTP 401)
    6. Authenticated access to /auth/me and /documents
    7. Cross-user isolation: User A cannot access User B's document (HTTP 403)
    8. Cleanup of provisioned test users from Supabase
    """
    db = get_db()
    assert db is not None, "Live Supabase client must be connected"

    # Generate unique test credentials with valid domain
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    email_a = f"test_user_{suffix_a}@moneydecode.com"
    email_b = f"test_user_{suffix_b}@moneydecode.com"
    pwd_a = "SecurePass123!A"
    pwd_b = "SecurePass123!B"

    user_a_id = None
    user_b_id = None
    token_a = None
    token_b = None

    try:
        # ====================================================================
        # 1. Sign up User A via API
        # ====================================================================
        print(f"Testing signup for User A ({email_a})...")
        signup_res_a = client.post("/auth/signup", json={"email": email_a, "password": pwd_a})
        assert signup_res_a.status_code == 201, f"Signup A failed: {signup_res_a.text}"
        data_a = signup_res_a.json()
        user_a_id = data_a["user_id"]
        token_a = data_a["access_token"]
        assert user_a_id, "User A must have a valid user_id"
        assert token_a, "User A must receive an access_token"
        print(f"User A created: {user_a_id}")

        # ====================================================================
        # 2. Sign up User B via API
        # ====================================================================
        print(f"Testing signup for User B ({email_b})...")
        signup_res_b = client.post("/auth/signup", json={"email": email_b, "password": pwd_b})
        assert signup_res_b.status_code == 201, f"Signup B failed: {signup_res_b.text}"
        data_b = signup_res_b.json()
        user_b_id = data_b["user_id"]
        token_b = data_b["access_token"]
        assert user_b_id, "User B must have a valid user_id"
        assert token_b, "User B must receive an access_token"
        print(f"User B created: {user_b_id}")

        # ====================================================================
        # 3. Successful Login
        # ====================================================================
        print("Testing login with valid credentials...")
        login_res = client.post("/auth/login", json={"email": email_a, "password": pwd_a})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        login_data = login_res.json()
        assert login_data["user_id"] == user_a_id
        assert login_data["access_token"]
        token_a = login_data["access_token"]
        print("Login succeeded!")

        # ====================================================================
        # 4. Incorrect Password Rejection
        # ====================================================================
        print("Testing login with incorrect password...")
        bad_login = client.post("/auth/login", json={"email": email_a, "password": "WrongPassword999!"})
        assert bad_login.status_code == 401, f"Expected 401 for bad password, got {bad_login.status_code}"
        print("Incorrect password correctly rejected with 401!")

        # ====================================================================
        # 5. Missing Authentication Token
        # ====================================================================
        print("Testing protected endpoint with missing token...")
        no_auth = client.get("/auth/me")
        assert no_auth.status_code == 401, f"Expected 401 without auth header, got {no_auth.status_code}"
        no_auth_docs = client.get("/documents")
        assert no_auth_docs.status_code == 401, f"Expected 401 on /documents, got {no_auth_docs.status_code}"
        print("Missing token correctly rejected with 401!")

        # ====================================================================
        # 6. Invalid / Expired Token
        # ====================================================================
        print("Testing protected endpoint with invalid token...")
        bad_token_res = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.signature-here"}
        )
        assert bad_token_res.status_code == 401, f"Expected 401 for bad token, got {bad_token_res.status_code}"
        print("Invalid token correctly rejected with 401!")

        # ====================================================================
        # 7. Authenticated Access to /auth/me
        # ====================================================================
        print("Testing authenticated /auth/me...")
        me_res = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert me_res.status_code == 200, f"/auth/me failed: {me_res.text}"
        me_data = me_res.json()
        assert me_data["user_id"] == user_a_id
        assert me_data["email"] == email_a
        print("Authenticated /auth/me succeeded!")

        # ====================================================================
        # 8. Cross-User Isolation (Tenant Isolation)
        # User A creates a document; User B attempts to access it -> 403 Forbidden!
        # ====================================================================
        print("Testing cross-user data isolation...")
        doc_a_id = str(uuid.uuid4())
        db.table("documents").insert({
            "id": doc_a_id,
            "user_id": user_a_id,
            "filename": "confidential_policy_user_a.pdf",
            "document_type": "health_insurance",
            "storage_path": f"documents/{doc_a_id}/policy.pdf",
            "status": "uploaded"
        }).execute()

        # User A accesses own document -> 200 OK
        doc_owner_res = client.get(
            f"/documents/{doc_a_id}",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert doc_owner_res.status_code == 200, f"Owner should access document: {doc_owner_res.text}"
        assert doc_owner_res.json()["id"] == doc_a_id

        # User B attempts to access User A's document -> 403 FORBIDDEN
        cross_res = client.get(
            f"/documents/{doc_a_id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert cross_res.status_code == 403, f"Cross-user access must return 403, got {cross_res.status_code}: {cross_res.text}"
        print("Cross-user access correctly blocked with 403 Forbidden!")

        # User B attempts to delete User A's document -> 403 FORBIDDEN
        cross_del = client.delete(
            f"/documents/{doc_a_id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert cross_del.status_code == 403, f"Cross-user delete must return 403, got {cross_del.status_code}"
        print("Cross-user delete correctly blocked with 403 Forbidden!")

        # Clean up test document
        db.table("documents").delete().eq("id", doc_a_id).execute()

    finally:
        # Cleanup provisioned test users from Supabase Auth & public.users
        admin_client = None
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        url = os.getenv("SUPABASE_URL")
        if url and service_key:
            from supabase import create_client as make_client
            admin_client = make_client(url, service_key)

        for uid in [user_a_id, user_b_id]:
            if uid:
                try:
                    db.table("users").delete().eq("id", uid).execute()
                except Exception:
                    pass
                if admin_client:
                    try:
                        admin_client.auth.admin.delete_user(uid)
                    except Exception:
                        pass
        print("Test users cleaned up successfully from Supabase.")


if __name__ == "__main__":
    test_supabase_auth_full_lifecycle()
    print("ALL SUPABASE AUTH TESTS PASSED AGAINST REAL SUPABASE INFRASTRUCTURE!")
