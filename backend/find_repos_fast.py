import os

desktop = r"C:\Users\Medora Gomes\Desktop"
print(f"Finding git repos in {desktop}...", flush=True)

for item in os.listdir(desktop):
    p = os.path.join(desktop, item)
    if os.path.isdir(p):
        git_dir = os.path.join(p, ".git")
        if os.path.exists(git_dir):
            print(f"Repo: {item}", flush=True)
            for f in os.listdir(p):
                if "env" in f.lower():
                    print(f"  env: {f}", flush=True)
                    try:
                        with open(os.path.join(p, f), "r", encoding="utf-8", errors="ignore") as envf:
                            for l in envf.readlines():
                                if any(k in l.lower() for k in ["postgres", "password", "supabase", "db_"]):
                                    print(f"    {l.strip()[:100]}", flush=True)
                    except Exception:
                        pass
print("Done.", flush=True)
