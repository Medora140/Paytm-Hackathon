import sqlite3
import shutil
import os

src = os.path.expanduser(r'~/AppData/Local/Microsoft/Edge/User Data/Default/History')
dst = 'hist_all.db'
shutil.copy2(src, dst)
conn = sqlite3.connect(dst)
cur = conn.cursor()
cur.execute("SELECT url, title, last_visit_time FROM urls WHERE url LIKE '%qtcncebuochelpgwqthx%' ORDER BY last_visit_time DESC")
for r in cur.fetchall():
    print(r)
conn.close()
if os.path.exists(dst):
    os.remove(dst)
