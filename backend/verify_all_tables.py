import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('backend/.env')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"Connecting to Supabase: {url}")
supabase = create_client(url, key)

tables = [
    'users',
    'documents',
    'document_chunks',
    'red_flags',
    'red_flag_patterns',
    'confidence_scores',
    'chat_messages',
    'benchmark_products',
    'scrape_jobs',
    'document_summaries'
]

results = {}
all_ok = True

for t in tables:
    try:
        res = supabase.table(t).select('*').limit(1).execute()
        results[t] = f"OK (status 200, count={len(res.data)})"
        print(f"Table '{t}': SUCCESS -> {results[t]}")
    except Exception as e:
        all_ok = False
        results[t] = f"FAILED: {e}"
        print(f"Table '{t}': ERROR -> {e}")

print("\n" + "="*50)
if all_ok:
    print(f"ALL {len(tables)} TABLES VERIFIED SUCCESSFULLY IN SUPABASE!")
else:
    print("SOME TABLES FAILED VERIFICATION.")
print("="*50)
