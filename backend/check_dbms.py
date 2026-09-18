import os

dbms_dir = r"C:\Users\Medora Gomes\Desktop\DBMS mini project"
print(f"Listing {dbms_dir}...", flush=True)

if os.path.exists(dbms_dir):
    for root, dirs, files in os.walk(dbms_dir):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "venv")]
        for f in files:
            p = os.path.join(root, f)
            print(f"  {p}", flush=True)
            if any(k in f.lower() for k in ["env", "sql", "config", "supabase", "db", "app", "server"]):
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                        print(f"--- Content of {f} ---", flush=True)
                        print(fl.read()[:500], flush=True)
                except Exception:
                    pass
