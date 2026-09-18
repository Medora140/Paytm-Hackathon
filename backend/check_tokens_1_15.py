import base64
import json
from extract_leveldb_tokens import unique_tokens

for idx, t in enumerate(unique_tokens):
    try:
        p_b64 = t.split('.')[1]
        p_b64 += '=' * (-len(p_b64) % 4)
        p = json.loads(base64.urlsafe_b64decode(p_b64))
        iss = p.get('iss', '')
        ref = p.get('ref', '')
        role = p.get('role', '')
        email = p.get('email', '')
        if any(k in str(p).lower() for k in ['supabase', 'qtcncebuochelpgwqthx', 'postgres', 'service_role', 'anon']):
            print(f"Token {idx+1}: iss={iss}, ref={ref}, role={role}, email={email}")
            print("  DATA:", p)
            print("  TOKEN:", t)
    except Exception as e:
        pass
