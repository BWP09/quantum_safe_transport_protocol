import socket, oqs, AES_cipher, threading, typing
import util

class Server:
    def __init__(self, kem_alg: str = "ML-KEM-512") -> None:
        self.kem_alg = kem_alg
        self._handler = None
        self._stopped = False

    def _init_socket(self, address: tuple[str, int], connections: int):
        self.address = address
        self._connections = connections

        self._sv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sv_socket.bind(self.address)
        self._sv_socket.listen(self._connections)

    def serve(self, address: tuple[str, int], connections: int = 10):
        self._init_socket(address, connections)

        self._threads: dict[str, threading.Thread] = {}

        while True:
            cl_socket, cl_addr = self._sv_socket.accept()

            if self._stopped:
                break

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
                    if self._handler:
                        resp = self._handler(req, addr)

                    else:
                        resp = req

                except Exception as e:
                    util.send_msg(sock, AES.encrypt(b"SERVER ERROR"))

                    del self._threads[name]

                    raise e

                util.send_msg(sock, AES.encrypt(resp))

                del self._threads[name]

            # proc = multiprocessing.Process(target = callback, name = thread_name, args = (cl_socket, cl_addr, thread_name))
            thread = threading.Thread(target = callback, name = thread_name, args = (cl_socket, cl_addr, thread_name))

            self._threads[thread_name] = thread

            thread.start()

        if self._stopped:
            for thread in self._threads.copy().values():
                thread.join(5)

            self._sv_socket.close()

    def close(self):
        self._stopped = True

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.address)
        sock.close()

    def handle_data(self, func: typing.Callable[[bytes, tuple[str, int]], bytes]) -> typing.Callable[[bytes, tuple[str, int]], bytes]:
        self._handler = func

        return func

if __name__ == "__main__":
    server = Server()

    @server.handle_data
    def handle(frame: bytes, addr: tuple[str, int]) -> bytes:
        print(f"connection from {addr}")

        if len(frame) < 100:
            print(f"data = {frame}")

        else:
            print(f"data = {frame[:100]}...")

        print(f"{len(frame) = }")

        return f"{addr[0]}:{addr[1]}".encode()

    server.serve(("0.0.0.0", 8080))