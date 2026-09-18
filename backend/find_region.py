import psycopg2

regions = [
    "ap-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "sa-east-1",
    "ca-central-1"
]

user = "postgres.qtcncebuochelpgwqthx"
dummy_pwd = "dummy_password_probe_123"

for r in regions:
    host = f"aws-0-{r}.pooler.supabase.com"
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=dummy_pwd,
            dbname="postgres",
            port=6543,
            connect_timeout=3,
            sslmode="require"
        )
        print(f"REGION MATCH! Connected to {r}")
        conn.close()
        break
    except psycopg2.OperationalError as e:
        msg = str(e).strip().splitlines()[0]
        if "ENOTFOUND" in msg:
            # tenant not in this region
            pass
        elif "password authentication failed" in msg:
            print(f"\n>>> FOUND PROJECT REGION: {r} <<<")
            print(f"    Message: {msg}\n")
            break
        else:
            print(f"Region {r}: {msg}")
    except Exception as e:
        print(f"Region {r} error: {e}")
print("Scan complete.")
