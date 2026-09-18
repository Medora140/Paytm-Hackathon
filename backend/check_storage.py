import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}"
}

r = httpx.get(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers)
print("Storage buckets status:", r.status_code)
print("Buckets:", r.text)
