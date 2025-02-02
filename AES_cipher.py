from Crypto.Cipher import AES as AES_
from Crypto.Util.Padding import pad, unpad

class AES:
    def __init__(self, key: bytes) -> None:
        self.key = key

    def encrypt(self, data: bytes):
        cipher = AES_.new(self.key, AES_.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES_.block_size))

        return bytes(cipher.iv) + ct_bytes

    def decrypt(self, data: bytes):
        iv = data[:16]
        ct = data[16:]
        cipher = AES_.new(self.key, AES_.MODE_CBC, iv)

        return unpad(cipher.decrypt(ct), AES_.block_size)
    
from Crypto.Random import get_random_bytes

def generate_key(n: int = 32) -> bytes:
    return get_random_bytes(n)