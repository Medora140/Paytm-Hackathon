import os
import json

paths = [
    r"C:\Users\Medora Gomes\AppData\Local\Google\Chrome\User Data\Default\Bookmarks",
    r"C:\Users\Medora Gomes\AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks"
]

for p in paths:
    if os.path.exists(p):
        print(f"Checking {p}...")
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
                if "supabase" in data.lower() or "qtcncebuochelpgwqthx" in data:
                    print("Found supabase in bookmarks!")
                    print(data[:500])
        except Exception as e:
            print(f"Error: {e}")
