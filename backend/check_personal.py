import os

folders = [
    r"C:\Users\Medora Gomes\Desktop\Personal stuff",
    r"C:\Users\Medora Gomes\Desktop\all documents",
    r"C:\Users\Medora Gomes\Desktop\Documents",
    r"C:\Users\Medora Gomes\Desktop\Firebase Credentials",
]

for folder in folders:
    if os.path.exists(folder):
        print(f"Checking {folder}...")
        for root, dirs, files in os.walk(folder):
            for f in files:
                p = os.path.join(root, f)
                if any(ext in f.lower() for ext in [".txt", ".env", ".json", ".md", ".pdf", ".sql"]):
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                            content = fl.read()
                            if any(k in content.lower() for k in ["supabase", "qtcncebuochelpgwqthx", "postgres", "password"]):
                                print(f"  MATCH in {p}:")
                                for l in content.splitlines()[:5]:
                                    print(f"    {l[:100]}")
                    except Exception:
                        pass
print("Done.")
