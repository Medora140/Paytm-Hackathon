import os
import shutil
import sqlite3

chrome_hist = os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data\Default\History")
temp_copy = os.path.join(os.getcwd(), "backend", "chrome_hist_temp.db")

print(f"Checking Chrome history: {chrome_hist}")
if os.path.exists(chrome_hist):
    try:
        shutil.copy2(chrome_hist, temp_copy)
        conn = sqlite3.connect(temp_copy)
        cur = conn.cursor()
        cur.execute("SELECT url, title, last_visit_time FROM urls WHERE url LIKE '%supabase%' ORDER BY last_visit_time DESC LIMIT 20")
        rows = cur.fetchall()
        print(f"Found {len(rows)} Supabase URLs in Chrome history:")
        for r in rows:
            print(f"  URL: {r[0]}")
            print(f"  Title: {r[1]}")
        conn.close()
        os.remove(temp_copy)
    except Exception as e:
        print(f"Error reading Chrome history: {e}")
