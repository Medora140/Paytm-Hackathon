import os

aiml_dir = r"C:\Users\Medora Gomes\Desktop\Aiml Hackathon"
print(f"Listing {aiml_dir}...", flush=True)

for root, dirs, files in os.walk(aiml_dir):
    dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "venv", "dist")]
    for f in files:
        p = os.path.join(root, f)
        print(f"  {p}", flush=True)
        if any(k in f.lower() for k in ["env", "sql", "config", "supabase", "db"]):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                    print(f"--- Content of {f} ---", flush=True)
                    print(fl.read()[:800], flush=True)
            except Exception as e:
                print(f"Error reading {f}: {e}")
