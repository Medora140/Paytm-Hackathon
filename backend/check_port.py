import socket
import psycopg2

try:
    s = socket.create_connection(("db.qtcncebuochelpgwqthx.supabase.co", 5432), timeout=3.0)
    s.close()
    print("Port 5432 is OPEN!")
except Exception as e:
    print(f"Port 5432 check failed: {e}")
