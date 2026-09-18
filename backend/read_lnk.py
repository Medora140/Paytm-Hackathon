import os

recent_dir = os.path.expandvars(r"%AppData%\Microsoft\Windows\Recent")
for name in ["Paytm1.0.lnk", "Paytm Hackathon.lnk", "paytm.lnk", "Money Docs Decoded.lnk"]:
    p = os.path.join(recent_dir, name)
    if os.path.exists(p):
        try:
            with open(p, "rb") as f:
                content = f.read()
                # extract printable ASCII strings
                import re
                strings = re.findall(rb"[A-Za-z0-9_:\\\.-]{5,}", content)
                decoded = [s.decode('latin1') for s in strings if "\\" in s.decode('latin1')]
                print(f"LNK {name}: {decoded[:3]}")
        except Exception as e:
            print(f"Error {name}: {e}")
