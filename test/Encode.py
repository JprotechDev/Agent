from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os, base64

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

def encrypt_aes(plain_text, password):
    ''' Mã hóa văn bản UTF-8 bằng AES-GCM với key từ password '''
    salt = os.urandom(16)  # Tạo salt
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode('utf-8'), None)
    return base64.b64encode(nonce + salt + ciphertext).decode('utf-8')

def decrypt_aes(ciphertext_base64, password):
    ''' Giải mã văn bản UTF-8 bằng AES-GCM với key từ password '''
    data = base64.b64decode(ciphertext_base64.encode('utf-8'))
    nonce, salt, ciphertext = data[:12], data[12:28], data[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    plain_text = aesgcm.decrypt(nonce, ciphertext, None)
    return plain_text.decode('utf-8')

# Ví dụ:
text = "Nguyễn Trọng Lâm"
#Mã hóa password
#password = base64.b64encode("jpt@2024".encode('utf-8')).decode('utf-8')
password = "anB0QDIwMjQ="
print("Password:", password)
enc = encrypt_aes(text, password)
print("Mã hóa:", enc)
dec = decrypt_aes(enc, password)
print("Giải mã:", dec)
