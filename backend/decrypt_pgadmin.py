import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.decrepit.ciphers.modes import CFB8

padding_string = b'}'
iv_size = AES.block_size // 8

def pad(key):
    if isinstance(key, str):
        key = key.encode()
    key = key[:32]
    if len(key) in (16, 24, 32):
        return key
    return key.ljust(32, padding_string)

def decrypt(ciphertext, key):
    # If hex encoded:
    try:
        ciphertext = bytes.fromhex(ciphertext)
    except:
        pass
    ciphertext = base64.b64decode(ciphertext)
    iv = ciphertext[:iv_size]
    cipher = Cipher(AES(pad(key)), CFB8(iv), default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext[iv_size:]) + decryptor.finalize()

ciphertexts = [
    '5150424c6245526552584f2f7675736d2b456e78504371317839313257744a37',
    '482b756647645641495941677743704964314159786a33372b62595a5a57586e'
]

keys_to_try = [
    'HuZRDvo0Ozp90zz2', # master password
    '831DENYFPQtAQ7_hYQpi5sFz7lD4C3iSNCdn82Oydiw=', # CSRF
    'F086FBYfS5a20EKEQmuNf9pK97SyiANQMGC5wkXE3MI=', # SECRET_KEY
    'd-0jNiW5L5lPwuVY37eY5TvrJkwEdp3_mru_Pb9F4IA=', # SECURITY_PASSWORD_SALT
    'a3ae6b883d2a47ffaf965ec2c87cee03', # user auth token
    '$pbkdf2-sha512$25000$YcyZcy5FqDWGkNK6t/ae8w$dWJLuw0yXgF7NLLKnDO3PdsbqsxRuUKpYnPMJB83HzDQLas1hfRXcqz2Wyzi4ay3Jw5hzJ9QUoqlD.lhd1PNqg'
]

for ct in ciphertexts:
    print(f"\n--- Testing Ciphertext {ct[:20]}... ---")
    for k in keys_to_try:
        try:
            res = decrypt(ct, k)
            print(f"Key {k[:20]:20}: Decrypted = {res.decode('utf-8', errors='ignore')}")
        except Exception as e:
            # print(f"Key {k[:20]:20}: Error {e}")
            pass
