import psycopg2
import time

host = "aws-0-ap-northeast-1.pooler.supabase.com"
user = "postgres.qtcncebuochelpgwqthx"
dbname = "postgres"
port = 6543

passwords = [
    # Snowy variations
    "Snowy@14",
    "Snowy@12",
    "Snowy@1402",
    "Snowy1402",
    "Snowy@1402#",
    "Snowy#1402",
    "Snowy@14#",
    "Snowy#14",
    "Snowy!14",
    "Snowy!1402",
    "Snowy@1402!",
    "Snowy1402!",
    "Snowy1402@",
    "Snowy@08",
    "Snowy@2024",
    "Snowy@2025",
    "Snowy@2026",
    "Snowy2026",
    "Snowy2025",
    "Snowy14",
    "Snowy12",
    "Snowy@1",
    "Snowy@2",
    "Snowy@1234",
    "Snowy1234",
    "Snowy@123",
    "Snowy123",
    "snowy@14",
    "snowy@1402",
    "snowy1402",
    
    # Medora / Carmelina variations
    "Medora@14",
    "Medora@1402",
    "Medora1402",
    "Medora@1402!",
    "Medora1402!",
    "Medora1402@",
    "Medora@12",
    "Medora#14",
    "Medora#1402",
    "Medora@2026",
    "Medora2026",
    "Medora@2025",
    "Medora2025",
    "Carmel@14",
    "Carmel@1402",
    "Carmelina@14",
    "Carmelina@1402",
    "carmelgomes1402",
    
    # Paytm variations
    "Paytm@123",
    "Paytm123",
    "Paytm@14",
    "Paytm@1402",
    "Paytm@2026",
    "Paytm2026",
    "PaytmHackathon@123",
    "PaytmHackathon123",
    "PaytmHackathon@2026",
    "PaytmHackathon",
    "paytm@123",
    "paytm123",
    "paytm@2026",
    
    # Supabase / Postgres defaults & project
    "qtcncebuochelpgwqthx",
    "postgres",
    "postgres123",
    "postgres@123",
    "MoneyDocs@1402",
    "MoneyDocs@14",
    "MoneyDocs@2026",
    "MoneyDocs2026",
]

found = None
for pwd in passwords:
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=pwd,
            dbname=dbname,
            port=port,
            connect_timeout=3,
            sslmode="require"
        )
        print(f"\n************************************************")
        print(f"SUCCESS! The PostgreSQL password is: {pwd}")
        print(f"************************************************\n", flush=True)
        found = pwd
        conn.close()
        break
    except psycopg2.OperationalError as e:
        msg = str(e).strip().splitlines()[0]
        print(f"Pwd {pwd:22}: {msg}")
    except Exception as e:
        print(f"Pwd {pwd:22} error: {e}")
    time.sleep(0.1)

if found:
    print(f"FINAL RESULT: FOUND = {found}")
else:
    print("Not found in initial list.")
