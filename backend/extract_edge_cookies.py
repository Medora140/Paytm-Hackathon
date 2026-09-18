import os
import json
import base64
import sqlite3
import shutil
import ctypes
from ctypes import wintypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Windows DPAPI
class DATA_BLOB(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_char))]

def dpapi_decrypt(encrypted_bytes):
    pDataIn = DATA_BLOB(len(encrypted_bytes), ctypes.cast(ctypes.create_string_buffer(encrypted_bytes), ctypes.POINTER(ctypes.c_char)))
    pDataOut = DATA_BLOB()
    if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(pDataIn), None, None, None, None, 0, ctypes.byref(pDataOut)):
        res = ctypes.string_at(pDataOut.pbData, pDataOut.cbData)
        ctypes.windll.kernel32.LocalFree(pDataOut.pbData)
        return res
    return None

# Get Edge encryption key
local_state_path = os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\User Data\Local State")
with open(local_state_path, "r", encoding="utf-8") as f:
    local_state = json.load(f)
encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
aes_key = dpapi_decrypt(encrypted_key)

# Copy Cookies DB
cookie_path = os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\User Data\Default\Network\Cookies")
temp_db = os.path.join(os.getcwd(), "backend", "edge_cookies_temp.db")
shutil.copy2(cookie_path, temp_db)

conn = sqlite3.connect(temp_db)
cur = conn.cursor()
cur.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%supabase%'")
rows = cur.fetchall()

tokens = {}
for host, name, enc_val in rows:
    if enc_val[:3] == b'v10':
        nonce = enc_val[3:15]
        ciphertext = enc_val[15:]
        aesgcm = AESGCM(aes_key)
        try:
            val = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
            print(f"Cookie: {name} on {host} = {val[:30]}...")
            tokens[name] = val
        except Exception as e:
            print(f"Decrypt error: {e}")

conn.close()
os.remove(temp_db)

# Save tokens to a test script
with open(os.path.join(os.getcwd(), "backend", "supabase_session.json"), "w") as f:
    json.dump(tokens, f)
print("Saved session tokens.")
