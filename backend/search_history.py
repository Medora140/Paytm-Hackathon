import os

user_dir = r"C:\Users\Medora Gomes"
candidate_files = [
    os.path.join(user_dir, ".bash_history"),
    os.path.join(user_dir, ".zsh_history"),
    os.path.join(user_dir, ".npmrc"),
    os.path.join(user_dir, ".gitconfig"),
    os.path.join(user_dir, ".env"),
]

for cf in candidate_files:
    if os.path.exists(cf):
        print(f"Reading {cf}:")
        with open(cf, "r", encoding="utf-8", errors="ignore") as f:
            print(f.read()[:500])

print("\nSearching Downloads and Desktop for any text files with password or supabase:")
for base in [os.path.join(user_dir, "Downloads"), os.path.join(user_dir, "Desktop")]:
    if not os.path.exists(base):
        continue
    for f in os.listdir(base):
        full = os.path.join(base, f)
        if os.path.isfile(full) and f.endswith((".txt", ".env", ".json", ".csv", ".md")):
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as fl:
                    cnt = fl.read()
                    if "supabase" in cnt.lower() or "qtcncebuochelpgwqthx" in cnt:
                        print(f"Found match in {full}!")
                        print(cnt[:300])
            except Exception:
                pass
