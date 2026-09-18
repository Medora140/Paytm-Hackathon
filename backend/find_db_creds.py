import os
import glob

search_dirs = [
    r"C:\Users\Medora Gomes\Desktop",
    r"C:\Users\Medora Gomes\Downloads",
    r"C:\Users\Medora Gomes\Documents",
]

print("Searching for candidate files mentioning supabase / postgresql / password...")
for sdir in search_dirs:
    if not os.path.exists(sdir):
        continue
    for root, dirs, files in os.walk(sdir):
        # Skip node_modules and .git and venv
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "venv", ".venv", ".next", "__pycache__")]
        for f in files:
            if f.endswith((".txt", ".md", ".env", ".json", ".sql", ".sh", ".py")):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as file:
                        content = file.read()
                        if "qtcncebuochelpgwqthx" in content or "db.qtcncebuochelpgwqthx" in content or "postgresql://postgres:" in content:
                            print(f"\nMATCH in {path}:")
                            for line in content.splitlines():
                                if any(k in line for k in ["postgres", "qtcncebuochelpgwqthx", "password", "DATABASE_URL"]):
                                    print("  ", line[:120])
                except Exception:
                    pass
print("\nSearch complete.")
