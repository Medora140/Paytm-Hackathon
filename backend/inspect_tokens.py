import sqlite3
import shutil
import os
import urllib.parse
import json

src = os.path.expanduser(r'~/AppData/Local/Microsoft/Edge/User Data/Default/History')
dst = 'history_tmp.db'
shutil.copy2(src, dst)
conn = sqlite3.connect(dst)
cur = conn.cursor()
cur.execute("SELECT url FROM urls WHERE url LIKE '%access_token=%'")
rows = cur.fetchall()
for r in rows:
    url = r[0]
    print("URL FOUND:", url[:100], "...")
    # parse the fragment or query
    if '#' in url:
        frag = url.split('#', 1)[1]
        params = urllib.parse.parse_qs(frag)
        for k, v in params.items():
            print(f"  {k} = {v[0][:50]}... (len={len(v[0])})")
            if k == 'access_token':
                print("  FULL ACCESS TOKEN:", v[0])
            if k == 'refresh_token':
                print("  FULL REFRESH TOKEN:", v[0])
conn.close()
if os.path.exists(dst):
    os.remove(dst)
