import os
import glob
import re
import json

ls_dir = os.path.expanduser(r'~/AppData/Local/Microsoft/Edge/User Data/Default/Local Storage/leveldb')
files = glob.glob(os.path.join(ls_dir, '*.ldb')) + glob.glob(os.path.join(ls_dir, '*.log'))

print(f"Scanning {len(files)} files in LevelDB...")
found_tokens = []

for f in sorted(files, key=os.path.getmtime, reverse=True):
    try:
        with open(f, 'rb') as fp:
            data = fp.read()
            # Look for supabase dashboard token patterns
            for pattern in [b'sb-', b'supabase', b'access_token', b'refresh_token', b'qtcncebuochelpgwqthx']:
                if pattern in data:
                    # Search for JWT tokens (eyJ...)
                    jwts = re.findall(rb'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', data)
                    for jwt in jwts:
                        jwt_str = jwt.decode('utf-8', errors='ignore')
                        # Decode header to check if it's Supabase
                        try:
                            parts = jwt_str.split('.')
                            header = json.loads(re.sub(r'[^a-zA-Z0-9_{}:",-]', '', os.popen(f'powershell -command "[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(\'{parts[0]}==\'))"').read().strip()) if False else {})
                        except:
                            pass
                        found_tokens.append((f, jwt_str))
    except Exception as e:
        pass

print(f"Found {len(found_tokens)} JWT matches:")
unique_tokens = list(set([t[1] for t in found_tokens]))
for idx, token in enumerate(unique_tokens):
    # Parse payload if possible
    try:
        import base64
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        iss = payload.get('iss', '')
        sub = payload.get('sub', '')
        exp = payload.get('exp', '')
        email = payload.get('email', '')
        ref = payload.get('ref', '')
        role = payload.get('role', '')
        print(f"\nToken {idx+1}:")
        print(f"  iss: {iss}, role: {role}, ref: {ref}, email: {email}, exp: {exp}")
        print(f"  FULL: {token}")
    except Exception as e:
        print(f"\nToken {idx+1} parse error {e}: {token[:80]}...")
