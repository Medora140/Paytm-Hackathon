import os
import ctypes
from ctypes import wintypes

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80

cookie_path = os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\User Data\Default\Network\Cookies")
handle = ctypes.windll.kernel32.CreateFileW(
    cookie_path,
    GENERIC_READ,
    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
    None,
    OPEN_EXISTING,
    FILE_ATTRIBUTE_NORMAL,
    None
)

print(f"CreateFile handle: {handle}")
if handle != -1 and handle != 0:
    print("SUCCESSFULLY opened locked Cookies file with shared read!")
    # Read first 100 bytes
    buf = ctypes.create_string_buffer(100)
    bytes_read = wintypes.DWORD()
    ctypes.windll.kernel32.ReadFile(handle, buf, 100, ctypes.byref(bytes_read), None)
    ctypes.windll.kernel32.CloseHandle(handle)
    print(f"Read {bytes_read.value} bytes: {buf.raw[:16]}")
else:
    err = ctypes.windll.kernel32.GetLastError()
    print(f"Failed with error code: {err}")
