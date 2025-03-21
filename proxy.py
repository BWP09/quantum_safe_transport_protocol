import typing
import server, client

class Proxy:
    def __init__(self, kem_alg: str = "ML-KEM-512") -> None:
        self.kem_alg = kem_alg
        self._server = server.Server(kem_alg)

        self._cl_handler = None
        self._sv_handler = None

    def serve(self, listen_address: tuple[str, int], upstream_address: tuple[str, int], connections: int = 10):
        @self._server.handle_data
        def _data_handler(frame: bytes, addr: tuple[str, int]) -> bytes:
            if self._cl_handler:
                frame = self._cl_handler(frame, addr)

            resp = client.Client(self.kem_alg).connect(upstream_address).do_request(frame)

            if self._sv_handler:
                resp = self._sv_handler(resp, addr)

            return resp

        self._server.serve(listen_address, connections)

    def close(self):
        self._server.close()

    def handle_client_data(self, func: typing.Callable[[bytes, tuple[str, int]], bytes]) -> typing.Callable[[bytes, tuple[str, int]], bytes]:
        self._cl_handler = func

        return func

    def handle_server_data(self, func: typing.Callable[[bytes, tuple[str, int]], bytes]) -> typing.Callable[[bytes, tuple[str, int]], bytes]:
        self._sv_handler = func

        return func

if __name__ == "__main__":
    proxy = Proxy()

    @proxy.handle_client_data
    def _cl_data_handler(frame: bytes, addr: tuple[str, int]) -> bytes:
        print("start server-bound route")

        print(f"connection from {addr}")

        if len(frame) < 100:
            print(f"data = {frame}")

        else:
            print(f"data = {frame[:100]}...")

        print(f"{len(frame) = }")

        print("end server-bound route")

        return frame + b" sv_bound proxy mutation"

    @proxy.handle_server_data
    def _sv_data_handler(frame: bytes, addr: tuple[str, int]) -> bytes:
        print(f"start client-bound route")

        print(f"client is {addr}")

        if len(frame) < 100:
            print(f"data = {frame}")

        else:
            print(f"data = {frame[:100]}...")

        print(f"{len(frame) = }")

        print(f"end client-bound route")

        return frame + b" cl_bound proxy mutation"

    proxy.serve(("0.0.0.0", 8081), ("127.0.0.1", 8080))