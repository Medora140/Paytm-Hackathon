import os
import requests
from dotenv import load_dotenv

load_dotenv('backend/.env')

url = os.getenv('SUPABASE_URL', '')
anon_key = os.getenv('SUPABASE_ANON_KEY', '')
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

endpoints = [
    '/pg/query',
    '/pg/v1/query',
    '/database/query',
    '/database/v1/query',
    '/sql',
    '/sql/v1',
    '/rest/v1/rpc/exec_sql',
    '/rest/v1/rpc/query',
    '/rest/v1/rpc/run_sql',
    '/rest/v1/rpc/execute_sql',
]

print(f"Testing endpoints on {url} with service_role key...")
for ep in endpoints:
    full_url = f"{url}{ep}"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(full_url, headers=headers, json={"query": "SELECT 1;"}, timeout=3)
        print(f"POST {ep}: status={r.status_code}, response={r.text[:100]}")
    except Exception as e:
        print(f"POST {ep}: error={e}")

print("Done probing.")
