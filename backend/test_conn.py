import psycopg2

passwords_to_try = [
    "Snowy123",
    "Snowy@123",
    "snowy123",
    "Snowy",
    "Medora123",
    "Medora@123",
    "Medora1402",
    "Medora@1402",
    "medora1402",
    "postgres",
    "postgres123",
    "MoneyDocs123",
    "MoneyDocs@123",
    "moneydocs123",
    "filmfest_db",
    "nyaysetu",
    "navoptima"
]

host = "db.qtcncebuochelpgwqthx.supabase.co"
user = "postgres"
dbname = "postgres"
port = 5432

for pwd in passwords_to_try:
    print(f"Testing password: {pwd} ...", flush=True)
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=pwd,
            dbname=dbname,
            port=port,
            connect_timeout=5,
            sslmode="require"
        )
        print(f"\n==========================================")
        print(f"SUCCESS! Password is: {pwd}")
        print(f"==========================================\n", flush=True)
        conn.close()
        break
    except psycopg2.OperationalError as e:
        err_msg = str(e).strip()
        print(f"  Failed: {err_msg.splitlines()[0]}")
    except Exception as e:
        print(f"  Other error: {e}")
