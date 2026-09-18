import os
import re

browser_dirs = [
    r"C:\Users\Medora Gomes\AppData\Local\Microsoft\Edge\User Data\Default\Local Storage\leveldb",
    r"C:\Users\Medora Gomes\AppData\Roaming\Mozilla\Firefox\Profiles",
    r"C:\Users\Medora Gomes\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Local Storage\leveldb"
]

for bdir in browser_dirs:
    if os.path.exists(bdir):
        print(f"Checking {bdir}...")
        for root, dirs, files in os.walk(bdir):
            for f in files:
                p = os.path.join(root, f)
                try:
                    with open(p, "rb") as fl:
                        data = fl.read()
                        sbp_matches = re.findall(b"sbp_[a-zA-Z0-9_-]{20,}", data)
                        if sbp_matches:
                            for m in sbp_matches:
                                print(f"FOUND sbp_ token in {p}: {m.decode('utf-8')}")
                except Exception:
                    pass
print("Browser check done.")
