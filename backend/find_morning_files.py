import os
import datetime

user_dir = r"C:\Users\Medora Gomes"
target_date = datetime.date(2026, 9, 18)

print("Files modified on 2026-09-18 between 08:00 and 11:30:")
search_paths = [
    r"C:\Users\Medora Gomes\Desktop",
    r"C:\Users\Medora Gomes\Downloads",
    r"C:\Users\Medora Gomes\AppData\Roaming\Code\User\History",
]

for sp in search_paths:
    if not os.path.exists(sp):
        continue
    for root, dirs, files in os.walk(sp):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "venv")]
        for f in files:
            p = os.path.join(root, f)
            try:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p))
                if mtime.date() == target_date and 8 <= mtime.hour <= 12:
                    print(f"  [{mtime.strftime('%H:%M:%S')}] {p} ({os.path.getsize(p)} bytes)")
            except Exception:
                pass
