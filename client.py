import typing, socket, oqs, AES_cipher
import util

class Client:
    def __init__(self, kem_alg: str = "ML-KEM-512") -> None:
        self.kem_alg = kem_alg
    
    def _init_socket_connection(self, remote_address: tuple[str, int]):
        self.remote_address = remote_address

        self._cl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._cl_socket.connect(remote_address)
    
    def _init_kem_tunnel(self):
        with oqs.KeyEncapsulation(self.kem_alg) as client:
            # Generate key pair
            public_key_client = client.generate_keypair()

            # Send public key to server
            self._cl_socket.sendall(public_key_client)

            # Recv cipher text from server
            cipher_text = self._cl_socket.recv(768)

            # Decapsulate cipher text to get key
            self._sh_secret = client.decap_secret(cipher_text)
    
    def connect(self, remote_address: tuple[str, int]) -> typing.Self:
        self._init_socket_connection(remote_address)
        self._init_kem_tunnel()

        return self

    def do_request(self, data: bytes) -> bytes:
        # Encrypt using shared secret and send data
        AES = AES_cipher.AES(self._sh_secret)

        enc_data = AES.encrypt(data)

        util.send_msg(self._cl_socket, enc_data)

        recv_data = util.recv_msg(self._cl_socket)

        self._cl_socket.close()

        if recv_data is None:
            raise Exception("message length was not defined")

        dec_data = AES.decrypt(recv_data)

        return dec_data

if __name__ == "__main__":
    class Requester:
        def __init__(self, host: str, port: int) -> None:
            self.host = host
            self.port = port

        def request(self, data: bytes) -> bytes:
            return Client().connect((self.host, self.port)).do_request(data)

    r = Requester("localhost", 8081)

    import random, time, os, hashlib

    ID = str(random.randint(0, 1000)).encode()

    requests = [
        # b"QSTP/1 GET /echo_body\n\n" + ID,
        # # b"QSTP/1 GET /time_test",
        # b"QSTP/1 GET /echo_body\n\n" + ID,
        # b"QSTP/1 GET /echo_body\n\n" + ID,
        # b"QSTP/1 GET /echo_body\n\n" + ID,
        # # b"QSTP/1 GET /time_test",
        # b"QSTP/1 GET /echo_body\n\n" + ID,

        # b"QSTP/1 GET /",
        # b"QSTP/1 POST /",
        # b"QSTP/1 POST /upload\nfile-name: test.txt\n\nfile content",
        # b"QSTP/1 POST /upload\nfile-name: test2.txt\n\nabcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnopqrstuvwxyz0123456789",
        # b"QSTP/1 DELETE /file\nfile-name: test.txt",
        # b"QSTP/1 DELETE /test\nfile-name: test.txt",
        # b"QSTP/1 POST /upload\n\nfile content",
        
        # b"QSTP/1 GET /argtest/ARGUMENT",
        # b"QSTP/1 GET /argtest/123",
        # b"QSTP/1 GET /argtest/456",
        # b"QSTP/1 GET /argtest/456/test",

        b"PROXY TEST server-bound data from client"
    ]

    # filename = "test_image.jpg"

    # with open(f"{os.getcwd()}/filetest/{filename}", "rb") as f:
    #     file_content = f.read()

    # file_len = len(file_content)
    # file_hash = hashlib.sha256(file_content).hexdigest()

    # print(f"file size: {file_len} bytes or {file_len / 1e6 :0.2f}MB")
    # print(f"file hash: {file_hash}")

    # requests = [
    #     f"QSTP/1 POST /upload\ncontent-length: {file_len}\ncontent-hash: {file_hash}\nfilename: {filename}\n\n".encode() + file_content,
    # ]

    for req in requests:
        print(f"REQ: {req[:100]}...")

        start = time.time()
        print(f"RSP: {r.request(req)}")    
        print(f"TIME -- {(time.time() - start) * 1000 :0.4f}ms")

        print("----------------")