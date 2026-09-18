import os
import datetime

temp_dir = os.path.expandvars(r"%LocalAppData%\Temp")
print(f"Checking {temp_dir} for files created/modified today...")
target_date = datetime.date(2026, 9, 18)

matches = []
for f in os.listdir(temp_dir):
    p = os.path.join(temp_dir, f)
    if os.path.isfile(p):
        try:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p))
            if mtime.date() == target_date:
                matches.append((mtime, p))
        except Exception:
            pass

matches.sort(key=lambda x: x[0], reverse=True)
print(f"Found {len(matches)} files from today:")
for mtime, p in matches[:30]:
    name = os.path.basename(p)
    print(f"  [{mtime.strftime('%H:%M:%S')}] {name} ({os.path.getsize(p)} bytes)")
    if any(k in name.lower() for k in ["env", "sql", "supa", "key", "pass", "token", "psql"]):
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                print(f"    Content: {fl.read()[:300]}")
        except Exception:
            pass
