import os
import json
import base64
import sqlite3
import ctypes
import ctypes.wintypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', ctypes.wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_char))
    ]

def decrypt_dpapi(cipher_text):
    blob_in = DATA_BLOB(len(cipher_text), ctypes.create_string_buffer(cipher_text))
    blob_out = DATA_BLOB()
    if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return data
    else:
        raise Exception("CryptUnprotectData failed")

def get_edge_key():
    local_state_path = os.path.expanduser(r'~/AppData/Local/Microsoft/Edge/User Data/Local State')
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    key = decrypt_dpapi(encrypted_key[5:])
    return key

def decrypt_cookie(encrypted_value, key):
    prefix = encrypted_value[:3]
    if prefix in (b'v10', b'v11', b'v20'):
        nonce = encrypted_value[3:15]
        ciphertext = encrypted_value[15:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8', errors='ignore')
    else:
        try:
            return decrypt_dpapi(encrypted_value).decode('utf-8', errors='ignore')
        except:
            return str(encrypted_value)

key = get_edge_key()
cookies_db = 'backend/cookies.db'

conn = sqlite3.connect(cookies_db)
cur = conn.cursor()
cur.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%supabase%'")
rows = cur.fetchall()
print(f"Found {len(rows)} cookies for supabase:")
cookies_dict = {}
for host, name, enc_val in rows:
    try:
        val = decrypt_cookie(enc_val, key)
        print(f"[{host}] {name} = {val[:60]}... (len={len(val)})")
        cookies_dict[name] = val
    except Exception as e:
        import traceback
        print(f"[{host}] {name} error: {e}")
        traceback.print_exc()

conn.close()

with open('backend/supabase_cookies.json', 'w') as f:
    json.dump(cookies_dict, f, indent=2)
print("Saved cookies to backend/supabase_cookies.json")
