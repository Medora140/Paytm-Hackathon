import socket

for h in ["aws-0-ap-south-1.pooler.supabase.com", "db.qtcncebuochelpgwqthx.supabase.co"]:
    for p in [6543, 5432]:
        try:
            s = socket.create_connection((h, p), timeout=3.0)
            s.close()
            print(f"{h}:{p} is OPEN!")
        except Exception as e:
            print(f"{h}:{p} FAILED: {e}")
