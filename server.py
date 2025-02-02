import socket, oqs, AES_cipher, threading, typing
import util

class Server:
    def __init__(self, kem_alg: str = "ML-KEM-512") -> None:
        self.kem_alg = kem_alg

    def _init_socket(self):
        self.sv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sv_socket.bind(self.address)
        self.sv_socket.listen(self.connections)

    def serve(self, address: tuple[str, int], connections: int = 10):
        self.address = address
        self.connections = connections

        self._init_socket()

        self.threads: dict[str, threading.Thread] = {}

        while True:
            cl_socket, cl_addr = self.sv_socket.accept()

            thread_name = f"{cl_addr[0]}:{cl_addr[1]}"

            def callback(sock: socket.socket, addr: tuple[str, int], name: str):
                # Recv client public key
                cl_public_key = sock.recv(800)

                with oqs.KeyEncapsulation(self.kem_alg) as server:
                    # Server generates and encapsulates secret using client's public key
                    cipher_text, sh_secret = server.encap_secret(cl_public_key)

                # Send cipher text to client
                sock.sendall(cipher_text)

                # Recv and decrypt data with shared secret
                AES = AES_cipher.AES(sh_secret)

                cipher_text = util.recv_msg(sock)

                if cipher_text is None:
                    raise Exception("message length was not defined")

                req = AES.decrypt(cipher_text)
                
                try:
                    resp = self.handler(req, addr)

                except Exception as e:
                    util.send_msg(sock, AES.encrypt(b"SERVER ERROR"))

                    del self.threads[name]

                    raise e

                util.send_msg(sock, AES.encrypt(resp))

                del self.threads[name]

            thread = threading.Thread(target = callback, name = thread_name, args = (cl_socket, cl_addr, thread_name))

            self.threads[thread_name] = thread

            thread.start()

    def handle_data(self, func: typing.Callable[[bytes, tuple[str, int]], bytes]) -> typing.Callable[[bytes, tuple[str, int]], bytes]:
        self.handler = func

        return func

if __name__ == "__main__":
    import time, random, os

    server = Server()

    @server.handle_data
    def handle(data: bytes, addr: tuple[str, int]) -> bytes:
        if len(data) < 1000:
            print(f"data: {data}")
        
        print(f"{len(data) = }")

        version, rest = data.split(b" ", 1)
        method, rest = rest.split(b" ", 1)
        path, rest = rest.split(b" ", 1)

        print(version, method)

        return b"200 OK"




        if data.startswith(b"GET"):
            method, version, path, _, data_ = data.split(b" ", 4)

            print(f"{method} (version {version}) path {path} with data: \"{data_ if len(data_) < 100 else f"{len(data_) = }"}\"")

            return "OK".encode()

        elif data.startswith(b"POST"):
            method, version, path, _, data_ = data.split(b" ", 4)

            print(f"{method} (version {version}) path {path} with data: \"{data_ if len(data_) < 100 else f"{len(data_) = }"}\"")

            if path == b"/upload":
                with open(f"{os.getcwd()}/output.png", "wb") as f:
                    f.write(data.split(b" : ", 1)[1])

                print("saved image to `output.png`")

            return "OK".encode()

        return "unknown method".encode()

    server.serve(("0.0.0.0", 8080))