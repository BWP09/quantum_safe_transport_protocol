import typing, socket, oqs, AES_cipher
import util

class Client:
    def __init__(self, kem_alg: str = "ML-KEM-512") -> None:
        self.kem_alg = kem_alg
    
    def _init_socket_connection(self):
        self.cl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cl_socket.connect(self.remote_address)
    
    def _init_kem_tunnel(self):
        with oqs.KeyEncapsulation(self.kem_alg) as client:
            # Generate key pair
            public_key_client = client.generate_keypair()

            # Send public key to server
            self.cl_socket.sendall(public_key_client)

            # Recv cipher text from server
            cipher_text = self.cl_socket.recv(768)

            # Decapsulate cipher text to get key
            self.sh_secret = client.decap_secret(cipher_text)
    
    def connect(self, remote_address: tuple[str, int]) -> typing.Self:
        self.remote_address = remote_address

        self._init_socket_connection()
        self._init_kem_tunnel()

        return self

    def do_request(self, data: bytes) -> bytes:
        # Encrypt using shared secret and send data
        AES = AES_cipher.AES(self.sh_secret)

        enc_data = AES.encrypt(data)

        # self.cl_socket.sendall(enc_data)
        util.send_msg(self.cl_socket, enc_data)

        recv_data = util.recv_msg(self.cl_socket)

        self.cl_socket.close()

        if recv_data is None:
            raise Exception("message length was not defined")

        dec_data = AES.decrypt(recv_data)

        return dec_data

class TextClient(Client):
    def __init__(self, kem_alg: str = "ML-KEM-512") -> None:
        super().__init__(kem_alg)

    def text_req(self, text: str) -> str:
        return self.do_request(text.encode()).decode()

class Requester:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def request(self, data: bytes) -> bytes:
        return Client().connect((self.host, self.port)).do_request(data)

def request(host: str, port: int, data: bytes) -> bytes:
    return Client().connect((host, port)).do_request(data)

# t1 = time.time()

# client = Client().connect(("localhost", 8080))

# t2 = time.time()

# data = client.do_request("GET 1 / : data".encode())

# t3 = time.time()

# print(f"resp: {data}")

# print(f"connect time -- {(t2 - t1) * 1000 :.5f}ms")
# print(f"req time -- {(t3 - t2) * 1000 :.5f}ms")
# print(f"total time -- {(t3 - t1) * 1000 :.5f}ms")

# client = TextClient().connect(("localhost", 8080))

# data = client.text_req("GET 1 / : data")

# print(data)

# for i in range(10):
#     print(request("localhost", 8080, b"GET 1 / : data"))

# import os

# with open(f"{os.getcwd()}/image.png", "rb") as f:
#     resp = request("localhost", 8080, "POST 1 /upload : ".encode() + f.read())

# print(resp)

# while True:
#     inp = input("> ")
    
#     if inp == "!exit":
#         break

#     resp = request("localhost", 8080, inp.encode())

#     print(resp)

r = Requester("localhost", 8080)

requests = [
    b"QSTP/1 GET /",
    b"QSTP/1 POST /",
    b"QSTP/1 POST /upload\nfile-name: test.txt\n\nfile content",
    b"QSTP/1 POST /upload\nfile-name: test2.txt\n\nabcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnopqrstuvwxyz0123456789",
    b"QSTP/1 DELETE /file\nfile-name: test.txt",
    b"QSTP/1 DELETE /test\nfile-name: test.txt",
    b"QSTP/1 POST /upload\n\nfile content",
]



for req in requests:
    print(f"REQ: {req}")
    print(f"RSP: {r.request(req)}")
    print("----------------")