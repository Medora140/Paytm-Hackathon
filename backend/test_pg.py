import socket
import psycopg2

hosts = [
    "db.qtcncebuochelpgwqthx.supabase.co",
    "aws-0-ap-south-1.pooler.supabase.com"
]

print("1. Testing DNS resolution and TCP port...")
for h in hosts:
    for port in [5432, 6543]:
        try:
            sock = socket.create_connection((h, port), timeout=3.0)
            sock.close()
            print(f"  SUCCESS: {h}:{port} is OPEN!")
        except Exception as e:
            print(f"  FAILED: {h}:{port} - {e}")
