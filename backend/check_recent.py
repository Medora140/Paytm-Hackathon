import os

recent_dir = os.path.expandvars(r"%AppData%\Microsoft\Windows\Recent")
print(f"Checking {recent_dir}...")
if os.path.exists(recent_dir):
    files = sorted(os.listdir(recent_dir), key=lambda x: os.path.getmtime(os.path.join(recent_dir, x)), reverse=True)
    print(f"Total recent items: {len(files)}")
    for f in files[:40]:
        print(f"  {f}")
