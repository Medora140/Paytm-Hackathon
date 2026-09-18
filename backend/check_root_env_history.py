import os
import json

hist_dir = r"C:\Users\Medora Gomes\AppData\Roaming\Code\User\History"
for entry in os.listdir(hist_dir):
    edir = os.path.join(hist_dir, entry)
    if not os.path.isdir(edir):
        continue
    ej = os.path.join(edir, "entries.json")
    if os.path.exists(ej):
        try:
            with open(ej, "r", encoding="utf-8", errors="ignore") as f:
                d = json.load(f)
                if "money-docs-decoded" in d.get("resource", "") and ".env" in d.get("resource", ""):
                    print(f"Resource: {d.get('resource')}")
                    for item in d.get("entries", []):
                        fpath = os.path.join(edir, item.get("id"))
                        if os.path.exists(fpath):
                            with open(fpath, "r", encoding="utf-8", errors="ignore") as fl:
                                print(f"  Entry {item.get('id')}:")
                                print(fl.read())
        except Exception:
            pass
