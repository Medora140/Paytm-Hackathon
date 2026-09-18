import os

dirs_to_check = [
    r"C:\Users\Medora Gomes\Desktop\Paytm Hackathon",
    r"C:\Users\Medora Gomes\Downloads\Money Docs Decoded",
]

for d in dirs_to_check:
    if os.path.exists(d):
        print(f"\nListing {d}:")
        for root, dirs, files in os.walk(d):
            dirs[:] = [sub for sub in dirs if sub not in ("node_modules", ".git", "venv")]
            for f in files:
                p = os.path.join(root, f)
                print(f"  {p} ({os.path.getsize(p)} bytes)")
    else:
        print(f"Path does not exist: {d}")
