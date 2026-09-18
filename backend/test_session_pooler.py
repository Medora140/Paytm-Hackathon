import psycopg2
import time

host = "aws-0-ap-northeast-1.pooler.supabase.com"
user = "postgres.qtcncebuochelpgwqthx"
dbname = "postgres"

test_pwds = [
    "Novarock123#",
    "Medora1402#",
    "Medora123#",
    "Snowy123#",
    "Paytm123#",
    "MoneyDocs123#",
    "Novarock@123",
    "Novarock123",
    "Medora@1402",
    "Snowy123"
]

for port in [5432, 6543]:
    print(f"\n--- Testing Port {port} ---")
    for pwd in test_pwds:
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
            print(f"!!! SUCCESS on port {port} with password: {pwd} !!!", flush=True)
            conn.close()
            exit(0)
        except psycopg2.OperationalError as e:
            msg = str(e).strip().splitlines()[0]
            print(f"Pwd {pwd:16} (port {port}): {msg}")
            if "ECIRCUITBREAKER" in msg:
                print("Circuit breaker active, stopping port", port)
                break
        time.sleep(1.0)
