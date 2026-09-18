import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json"
}

routes = [
    "/rest/v1/",
    "/rest/v1/rpc",
    "/auth/v1/health",
    "/storage/v1/bucket",
    "/pg/query",
    "/pg/v1/query",
    "/pg/query/v1",
    "/pg-meta/query",
    "/pg-meta/v1/query",
    "/platform/query",
    "/database/query",
    "/sql",
    "/v1/query",
    "/query",
    "/api/query",
    "/api/v1/query",
    "/meta/query",
    "/meta/v1/query",
    "/rpc/exec_sql",
    "/rest/v1/rpc/exec",
    "/rest/v1/rpc/execute",
    "/rest/v1/rpc/sql",
    "/rest/v1/rpc/run_sql"
]

print("Probing routes on Supabase host...")
for r in routes:
    url = f"{SUPABASE_URL}{r}"
    try:
        resp = httpx.post(url, headers=headers, json={"query": "SELECT 1;"}, timeout=4.0)
        print(f"POST {r:25} -> {resp.status_code} : {resp.text[:80]}")
    except Exception as e:
        print(f"POST {r:25} -> ERR: {e}")
