import sqlite3
import os

db_path = os.path.expanduser(r'~/AppData/Roaming/pgadmin/pgadmin4.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", [r[0] for r in cur.fetchall()])

try:
    cur.execute("SELECT id, name, host, port, maintenance_db, username, password FROM server;")
    rows = cur.fetchall()
    print(f"Found {len(rows)} servers:")
    for r in rows:
        print(f"Server ID {r[0]}: Name={r[1]}, Host={r[2]}, Port={r[3]}, DB={r[4]}, User={r[5]}, PwdEnc={bool(r[6])}")
except Exception as e:
    print("Error querying server:", e)

conn.close()
