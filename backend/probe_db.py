import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

print(f"Testing Supabase URL: {SUPABASE_URL}")
print(f"Using key starting with: {SUPABASE_KEY[:10]}...")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# 1. Test OpenAPI schema from PostgREST to see all exposed tables
resp = httpx.get(f"{SUPABASE_URL}/rest/v1/?apikey={SUPABASE_KEY}", headers=headers, timeout=10.0)
print(f"OpenAPI Schema status: {resp.status_code}")
if resp.status_code == 200:
    spec = resp.json()
    definitions = spec.get("definitions", {})
    paths = spec.get("paths", {})
    print("Tables found in PostgREST definitions:")
    for t in sorted(definitions.keys()):
        print(f"  - {t}")
    print("Paths found in PostgREST:")
    for p in sorted(paths.keys()):
        if p != "/":
            print(f"  - {p}")
else:
    print(f"Error fetching schema: {resp.text[:300]}")

# 2. Test direct queries for each expected table
expected_tables = [
    "users",
    "documents",
    "document_chunks",
    "document_summaries",
    "red_flags",
    "red_flag_patterns",
    "confidence_scores",
    "chat_messages",
    "benchmark_products",
    "scrape_jobs"
]

print("\nDirect table query tests via PostgREST:")
for table in expected_tables:
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/{table}?select=count", headers=headers, timeout=5.0)
    print(f"  Table '{table}': HTTP {r.status_code} - {r.text[:100]}")

# 3. Test if SQL execution endpoints exist
sql_endpoints = [
    f"{SUPABASE_URL}/pg/query",
    f"{SUPABASE_URL}/pg/v1/query",
    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
    f"{SUPABASE_URL}/rest/v1/rpc/query"
]
print("\nTesting SQL endpoints:")
for ep in sql_endpoints:
    try:
        r = httpx.post(ep, headers=headers, json={"query": "SELECT 1;"}, timeout=5.0)
        print(f"  Endpoint {ep}: HTTP {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"  Endpoint {ep}: Exception {e}")
