import sqlite3
import shutil
import os

for browser in [r'Microsoft\Edge', r'Google\Chrome']:
    src = os.path.expanduser(f'~/AppData/Local/{browser}/User Data/Default/History')
    if os.path.exists(src):
        bname = 'edge' if 'Edge' in browser else 'chrome'
        dst = f'history_{bname}.db'
        try:
            shutil.copy2(src, dst)
            conn = sqlite3.connect(dst)
            cur = conn.cursor()
            cur.execute('SELECT url, title FROM urls WHERE url LIKE ? ORDER BY last_visit_time DESC LIMIT 30', ('%supabase%',))
            rows = cur.fetchall()
            print(f'=== {browser} Supabase URLs ===')
            for r in rows:
                print(r)
            conn.close()
            if os.path.exists(dst):
                os.remove(dst)
        except Exception as e:
            print(f'Error reading {browser}: {e}')
