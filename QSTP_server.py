import typing, rich.console
import server, QSTP

class QSTP_Server:
    def __init__(self) -> None:
        self._server = server.Server()
        self._router = Router()

        self.route = self._router.route
        self._handler = None

        @self._server.handle_data
        def _data_handler(frame: bytes, addr: tuple[str, int]) -> bytes:
            req = QSTP.Request.from_frame(frame, addr)

            if isinstance(req, QSTP.Response):
                return req.to_frame()

            try:
                if self._handler:
                    return self._handler(req).to_frame()

                elif (ret := self._router.match_route(req.path, req.method)):
                    return ret[0](req, ret[1]).to_frame()

                else:
                    return QSTP.Response(204, headers = {"request-method": req.method, "request-path": req.path}).to_frame()
            
            except:
                rich.console.Console().print_exception()

                return QSTP.Response(101).to_frame()

    def serve(self, address: tuple[str, int]):
        self._server.serve(address)

    def close(self):
        self._server.close()

    def handle_data(self, func: typing.Callable[[QSTP.Request], QSTP.Response]) -> typing.Callable[[QSTP.Request], QSTP.Response]:
        self._handler = func

        return func

class Router:
    def __init__(self) -> None:
        self.handlers: dict[str, dict[str, typing.Callable[[QSTP.Request, dict[str, str]], QSTP.Response]]] = {}

        for method in QSTP.METHODS:
            self.handlers[method] = {}

    def route(self, route_descriptor: str, methods: list[str] | None = None):
        def decorator(func: typing.Callable[[QSTP.Request, dict[str, str]], QSTP.Response]):
            methods_ = methods or ["GET"]

            for method in methods_:
                if method not in QSTP.METHODS:
                    raise Exception(f"Unknown method {method!r}")

                self.handlers[method][route_descriptor] = func

            return func

        return decorator

    def match_route(self, route_descriptor: str, method: str) -> tuple[typing.Callable[[QSTP.Request, dict[str, str]], QSTP.Response], dict[str, str]] | None:
        if method not in QSTP.METHODS:
            raise Exception(f"Unknown method {method!r}")

        for defined_route, func in self.handlers[method].items():
            path_defined = []
            path_try = []

            for part in defined_route.split("/"):
                if part.startswith("<") and part.endswith(">"):
                    path_defined.append((1, part[1:-1]))

                elif part:
                    path_defined.append((0, part))

            path_try = list(filter(lambda x: bool(x), route_descriptor.split("/")))

            if len(path_defined) != len(path_try):
                continue

            variables = {}

            for defined, test in zip(path_defined, path_try):
                if defined[0] == 0 and defined[1] == test:
                    continue

                elif defined[0] == 1:
                    variables[defined[1]] = test

                else:
                    break

            else:
                return func, variables


if __name__ == "__main__":
    import time, os, hashlib, sys

    sv = QSTP_Server()

    @sv.route("/")
    def index(rq: QSTP.Request, _) -> QSTP.Response:
        print(rq)

        resp = QSTP.Response(200, headers = {"origin-method": rq.method}, data = b"test data")

        print(resp)

        return resp
    
    @sv.route("/test")
    def test(rq: QSTP.Request, _) -> QSTP.Response:
        print(rq)

        if rq.headers and rq.headers.get("test-shutdown") == "finish request":
            print("shutdown header found, closing server...")

            sv.close()

        return QSTP.Response(200, headers = {"Content-Type": "text/plaintext"}, data = f"hello {rq.headers.get("Proxied-For") if rq.headers else ""} from server on port {sys.argv[1]}".encode())

    @sv.route("/time_test")
    def time_test(rq: QSTP.Request, _) -> QSTP.Response:
        if rq.data:
            time.sleep(int(rq.data))

        else:
            time.sleep(1)

        return QSTP.Response(200, headers = rq.headers)

    @sv.route("/echo")
    def echo(rq: QSTP.Request, _) -> QSTP.Response:
        return QSTP.Response(200, headers = rq.headers, data = rq.data)

    @sv.route("/argtest/<arg1>")
    def argtest(rq: QSTP.Request, args: dict[str, str]) -> QSTP.Response:
        print(args)

        return QSTP.Response(200, data = str(args).encode())

    @sv.route("/upload", methods = ["POST"])
    def upload(rq: QSTP.Request, _) -> QSTP.Response:
        print(f"Headers: {rq.headers}")

        if not rq.headers:
            return QSTP.Response(201, data = b"Need headers!")

        if not (filename := rq.headers.get("filename")):
            return QSTP.Response(201, data = b"Need filename header!")

        if not (content_len := rq.headers.get("content-length")):
            return QSTP.Response(201, data = b"Need content-length header!")

        if not (content_hash := rq.headers.get("content-hash")):
            return QSTP.Response(201, data = b"Need content-hash header!")

        if not (content := rq.data):
            return QSTP.Response(201, data = b"Need file content!")

        file_len = len(content)
        file_hash = hashlib.sha256(content).hexdigest()

        print(f"data lengths match: {file_len == int(content_len)}")
        print(f"data hashes match: {file_hash == content_hash}")

        with open(f"{os.getcwd()}/filetest/SERVER_OUTPUT__{filename}", "wb") as f:
            f.write(content)

        return QSTP.Response(200)

    sv.serve(("0.0.0.0", int(sys.argv[1])))