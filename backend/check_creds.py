import os
import glob
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
PROJECT_REF = "qtcncebuochelpgwqthx"

print("Checking home directory for supabase config...")
home = os.path.expanduser("~")
supabase_dirs = glob.glob(os.path.join(home, ".supabase*"))
print("Found ~/.supabase*: ", supabase_dirs)
for d in supabase_dirs:
    if os.path.isfile(d):
        print(f"File: {d}")
    else:
        print(f"Dir: {d}, contents: {os.listdir(d)}")

# Check if there is any access token in ~/.supabase/access_token
token_file = os.path.join(home, ".supabase", "access_token")
if os.path.exists(token_file):
    with open(token_file, "r") as f:
        print("Found access_token in ~/.supabase/access_token!")

# Check common Supabase CLI configs
config_file = os.path.join(home, ".config", "supabase")
if os.path.exists(config_file):
    print("Found ~/.config/supabase:", os.listdir(config_file))

# Test Supabase Management API with SERVICE_KEY just in case
print("\nTesting Supabase Management API with service role key:")
for token in [SERVICE_KEY]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = httpx.post(
            f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
            headers=headers,
            json={"query": "SELECT 1;"},
            timeout=5.0
        )
        print(f"api.supabase.com query status: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"api.supabase.com exception: {e}")
