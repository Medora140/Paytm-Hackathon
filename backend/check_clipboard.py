import os

clip_dir = os.path.expandvars(r"%LocalAppData%\Microsoft\Windows\Clipboard")
print(f"Checking {clip_dir}...")
if os.path.exists(clip_dir):
    for root, dirs, files in os.walk(clip_dir):
        for f in files:
            p = os.path.join(root, f)
            print(f"  {p} ({os.path.getsize(p)} bytes)")
else:
    print("Clipboard dir not found.")
