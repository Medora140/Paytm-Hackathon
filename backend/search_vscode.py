import os

vscode_dir = r"C:\Users\Medora Gomes\AppData\Roaming\Code"
print("Searching VS Code directories for 'qtcncebuochelpgwqthx' or 'supabase'...")
for root, dirs, files in os.walk(vscode_dir):
    for f in files:
        if f.endswith((".json", ".vscdb", ".log", ".txt")):
            p = os.path.join(root, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as file:
                    data = file.read()
                    if "qtcncebuochelpgwqthx" in data:
                        print(f"\nFOUND in {p}:")
                        for line in data.splitlines():
                            if "qtcncebuochelpgwqthx" in line:
                                print(f"  {line[:150]}")
            except Exception:
                pass
print("\nSearch done.")
