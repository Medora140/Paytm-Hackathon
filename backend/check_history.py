import os
import json

hist_dir = r"C:\Users\Medora Gomes\AppData\Roaming\Code\User\History"
print(f"Checking {hist_dir}...", flush=True)

if os.path.exists(hist_dir):
    entries = os.listdir(hist_dir)
    print(f"Total history entries: {len(entries)}", flush=True)
    for entry in entries:
        edir = os.path.join(hist_dir, entry)
        if not os.path.isdir(edir):
            continue
        entries_json = os.path.join(edir, "entries.json")
        if os.path.exists(entries_json):
            try:
                with open(entries_json, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    resource = data.get("resource", "")
                    if any(k in resource.lower() for k in [".env", "database", "schema", "config"]):
                        print(f"Found match: {resource} in {entry}", flush=True)
                        for file_entry in data.get("entries", []):
                            fid = file_entry.get("id")
                            fpath = os.path.join(edir, fid)
                            if os.path.exists(fpath):
                                with open(fpath, "r", encoding="utf-8", errors="ignore") as fl:
                                    print(f"--- Content of {fid} ({resource}) ---", flush=True)
                                    print(fl.read()[:500], flush=True)
            except Exception:
                pass
print("History check complete.", flush=True)
