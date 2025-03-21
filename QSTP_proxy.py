import typing
import proxy, QSTP

class QSTP_Proxy:
    def __init__(self) -> None:
        self._proxy = proxy.Proxy()

        self._cl_handler = None
        self._sv_handler = None

    def serve(self, listen_address: tuple[str, int], upstream_address: tuple[str, int]):
        self._proxy.serve(listen_address, upstream_address)

    def close(self):
        self._proxy.close()

    def handle_client_data(self, func: typing.Callable[[QSTP.Request], QSTP.Request]) -> typing.Callable[[QSTP.Request], QSTP.Request]:
        @self._proxy.handle_client_data
        def _cl_data_handler(frame: bytes, addr: tuple[str, int]) -> bytes:
            req = QSTP.Request.from_frame(frame, addr)

            if isinstance(req, QSTP.Response):
                return req.to_frame()

            return func(req).to_frame()

        return func

    def handle_server_data(self, func: typing.Callable[[QSTP.Response], QSTP.Response]) -> typing.Callable[[QSTP.Response], QSTP.Response]:
        @self._proxy.handle_server_data
        def _sv_data_handler(frame: bytes, addr: tuple[str, int]) -> bytes:
            req = QSTP.Response.from_frame(frame)

            return func(req).to_frame()

        return func

if __name__ == "__main__":
    proxy_ = QSTP_Proxy()

    @proxy_.handle_client_data
    def _cl_data_handler(rq: QSTP.Request) -> QSTP.Request:
        print(f"incoming: {rq}")

        # if rq.data is not None:
        #     rq.data += b" cl_mod"

        print(f"outbound: {rq}")

        return rq

    @proxy_.handle_server_data
    def _sv_data_handler(rsp: QSTP.Response) -> QSTP.Response:
        print(f"incoming: {rsp}")

        # if rsp.data is not None:
        #     rsp.data += b" sv_mod"

        print(f"outbound: {rsp}")

        return rsp

    proxy_.serve(("0.0.0.0", 8081), ("localhost", 8080))