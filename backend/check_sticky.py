import os
import sqlite3

sticky_path = os.path.expandvars(r"%LocalAppData%\Packages\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\LocalState\plum.sqlite")
print(f"Checking Sticky Notes at: {sticky_path}")
if os.path.exists(sticky_path):
    try:
        conn = sqlite3.connect(sticky_path)
        cur = conn.cursor()
        cur.execute("SELECT Text FROM Note")
        rows = cur.fetchall()
        print(f"Found {len(rows)} sticky notes:")
        for r in rows:
            print("--- NOTE ---")
            print(r[0][:500])
        conn.close()
    except Exception as e:
        print(f"Error reading sticky notes: {e}")
else:
    print("Sticky notes DB not found.")
