import typing
import client, QSTP

class QSTP_Client:
    def __init__(self) -> None:
        self._client = client.Client()

    def request_obj(self, request: QSTP.Request) -> QSTP.Response:
        try:
            return QSTP.Response.from_frame(self._client.connect(request.address).do_request(request.to_frame()))

        except ConnectionRefusedError:
            return QSTP.Response(1)
        
    def request(self, address: tuple[str, int], method: str, path: str, headers: dict[str, str] | None = None, data: bytes | None = None) -> QSTP.Response:
        return self.request_obj(QSTP.Request(address, method, path, headers, data))

if __name__ == "__main__":
    import sys, time

    address = ("localhost", int(sys.argv[1]))

    client_ = QSTP_Client()

    requests = [
        # (address, "GET", "/test", {"Host": "server1.com"}, b"test data from client looking for server 1"),
        # (address, "GET", "/test", {"Host": "server2.com", "test-shutdown": "finish request"}, b"test data from client looking for server 2"),
        # (address, "GET", "/test", {"Host": "server3.com"}, b"test data from client looking for server 3"),
        # (address, "GET", "/test", {"Host": "server2.com"}, b"test data from client looking for server 2"),

        (address, "GET", "/echo", {"header-test": "test-header"}, b"test data from client"),
    ]

    for i, req in enumerate(requests):
        print(f" -- {i + 1}/{len(requests)} -- ")

        t1 = time.time()
        print(client_.request(*req))
        t2 = time.time()

        print(f"{(t2 - t1) * 1000 :.5f}ms")

        if i + 1 != len(requests):
            time.sleep(0.5)