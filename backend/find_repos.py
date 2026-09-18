import os

desktop = r"C:\Users\Medora Gomes\Desktop"
print(f"Finding git repos in {desktop}...")
for root, dirs, files in os.walk(desktop):
    if ".git" in dirs:
        dirs.remove(".git")
        print(f"Git repo: {root}")
        # Look for .env files or commit history in this repo
        for f in os.listdir(root):
            if "env" in f.lower():
                print(f"   found env file: {os.path.join(root, f)}")
