import os

for k, v in os.environ.items():
    if "SUPABASE" in k or "TOKEN" in k or "KEY" in k:
        print(f"ENV: {k} = {v[:15]}...")

supa_dir = os.path.expanduser("~/.supabase")
if os.path.exists(supa_dir):
    for root, dirs, files in os.walk(supa_dir):
        for f in files:
            p = os.path.join(root, f)
            print(f"File in .supabase: {p} ({os.path.getsize(p)} bytes)")
            try:
                with open(p, "r", errors="ignore") as fl:
                    head = fl.read(200)
                    print(f"  Head: {head[:100]}")
            except Exception as e:
                print(f"  Error: {e}")
