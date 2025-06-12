from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os

class Encdec:
    @staticmethod
    def derive_key(password, salt):
        ''' Sinh khóa AES 128-bit từ password và salt '''
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=16,  # 128-bit
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))

    @staticmethod
    def encrypt_aes(plain_text, password):
        salt = b"mysalt1234567890"[:16]
        nonce = b"mynonce123456"[:12]
        key = Encdec.derive_key(password, salt)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plain_text.encode('utf-8'), None)
        return (nonce + salt + ciphertext).hex()

    @staticmethod
    def decrypt_aes(ciphertext_hex, password):
        try:
            data = bytes.fromhex(ciphertext_hex)
            key = Encdec.derive_key(password, data[12:28])
            return AESGCM(key).decrypt(data[:12], data[28:], None).decode('utf-8')
        except Exception:
            return ciphertext_hex

'''# Ví dụ:
text = "20212816@eaut.edu.vn"
password = "97c1e9ccdf80b8e77a0b07c1c5c1ab71"  # md5 hash của "jpt@2024"

# Mã hóa
enc = Encdec.encrypt_aes(text, password)
print("Mã hóa (HEX):", enc)

# Giải mã
dec = Encdec.decrypt_aes(enc, password)
print("Giải mã:", dec)
'''