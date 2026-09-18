import os
import shutil
import sqlite3

hist_path = os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\User Data\Default\History")
temp_copy = os.path.join(os.getcwd(), "backend", "edge_hist_temp.db")

print(f"Checking Edge history: {hist_path}")
if os.path.exists(hist_path):
    try:
        shutil.copy2(hist_path, temp_copy)
        conn = sqlite3.connect(temp_copy)
        cur = conn.cursor()
        cur.execute("SELECT url, title, last_visit_time FROM urls WHERE url LIKE '%supabase%' ORDER BY last_visit_time DESC LIMIT 20")
        rows = cur.fetchall()
        print(f"Found {len(rows)} Supabase URLs in Edge history:")
        for r in rows:
            print(f"  URL: {r[0]}")
            print(f"  Title: {r[1]}")
        conn.close()
        os.remove(temp_copy)
    except Exception as e:
        print(f"Error reading Edge history: {e}")
