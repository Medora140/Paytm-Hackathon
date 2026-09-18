import os
import re

chrome_dir = r"C:\Users\Medora Gomes\AppData\Local\Google\Chrome\User Data\Default\Local Storage\leveldb"
print(f"Checking {chrome_dir}...", flush=True)

if os.path.exists(chrome_dir):
    for f in os.listdir(chrome_dir):
        p = os.path.join(chrome_dir, f)
        if os.path.isfile(p):
            try:
                with open(p, "rb") as fl:
                    data = fl.read()
                    # Look for sbp_ tokens (Supabase Personal Access Tokens)
                    sbp_matches = re.findall(b"sbp_[a-zA-Z0-9_-]{20,}", data)
                    if sbp_matches:
                        for m in sbp_matches:
                            print(f"FOUND sbp_ token in {f}: {m.decode('utf-8')}", flush=True)
                    
                    # Look for supabase tokens or session
                    if b"supabase" in data.lower():
                        # Search for access_token or token patterns
                        token_matches = re.findall(b'sb-[a-zA-Z0-9]+-auth-token', data)
                        if token_matches:
                            print(f"Found auth keys in {f}: {token_matches}", flush=True)
            except Exception as e:
                pass
print("Chrome leveldb check done.", flush=True)
