import os
import sys

brain_dir = r"C:\Users\Medora Gomes\.gemini\antigravity"
print(f"Searching in {brain_dir}...", flush=True)

matches = []
for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if f.endswith((".json", ".md", ".txt", ".log")):
            p = os.path.join(root, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                    content = fl.read()
                    if "qtcncebuochelpgwqthx" in content:
                        print(f"MATCH in {p}", flush=True)
                        for line in content.splitlines():
                            if any(k in line.lower() for k in ["postgres", "password", "postgresql://", "secret", "database_url", "sbp_"]):
                                print(f"  {line[:150]}", flush=True)
            except Exception:
                pass
print("Done.", flush=True)
