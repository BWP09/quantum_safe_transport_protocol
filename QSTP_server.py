import typing
import server

VERSION = "QSTP/1"

status_codes = {
    100: "SERVER OK",
    101: "SERVER ERROR",
    200: "OK",
    201: "MALFORMED",
    202: "UNKNOWN VERSION",
    203: "UNKNOWN METHOD",
    204: "UNKNOWN PATH",
    205: "UNAUTHENTICATED",
    206: "UNAUTHORIZED",
}

METHODS = {
    "GET",
    "POST",
    "DELETE",
    "PATCH",
}

class Request:
    def __init__(self, addr: tuple[str, int], method: str, path: str, headers: dict[str, str] | None = None, data: bytes | None = None) -> None:
        if method not in METHODS:
            raise ValueError(f"{method} is not a method")
        
        self.addr = addr
        self.method = method
        self.path = path
        self.headers = headers
        self.data = data
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(addr = {self.addr}, method = {self.method!r}, path = {self.path!r}{f", headers = {self.headers}" if self.headers else ""}{f", data = {self.data[:50]}{"..." if len(self.data) > 50 else ""}" if self.data else ""})"

    @staticmethod
    def parse_headers(headers: str) -> dict[str, str]:
        headers_out = {}

        for line in headers.split("\n"):
            k, v = line.split(":", 1)

            headers_out[k.strip()] = v.strip()

        return headers_out

class Response:
    def __init__(self, status_code: int, headers: dict | None = None, data: bytes | None = None) -> None:
        if status_code not in status_codes.keys():
            raise ValueError(f"{status_code} is not a valid status code")
        
        self.status_code = status_code
        self.headers = headers
        self.data = data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_code = {self.status_code}{f", headers = {self.headers}" if self.headers else ""}{f", data = {self.data[:50]}{"..." if len(self.data) > 50 else ""}" if self.data else ""})"

    def to_frame(self) -> bytes:
        head = f"{VERSION} {self.status_code} {status_codes[self.status_code]}{("\n" + "\n".join(f"{k}: {v}" for k, v in self.headers.items())) if self.headers else ""}\n"

        return head.encode() + (b"\n" + self.data if self.data else b"")

class QSTP_Server:
    def __init__(self) -> None:
        self._server = server.Server()
        self._router = Router()
        self.route = self._router.route

        @self._server.handle_data
        def _data_handler(frame: bytes, addr: tuple[str, int]) -> bytes:
            frame_split = frame.split(b"\n\n", 1)

            if len(frame_split) == 1:
                frame_split = [frame_split[0], b""]

            head, data = frame_split

            head = head.decode()

            head_split = head.split("\n", 1)

            if len(head_split) == 1:
                head_split = [head_split[0], ""]

            info_line, headers_raw = head_split

            info_line_split = info_line.split(" ", 2)

            if len(info_line_split) != 3:
                return Response(201).to_frame()
            
            version, method, path = info_line_split

            if version != VERSION:
                return Response(202).to_frame()
            
            if method not in METHODS:
                return Response(203).to_frame()
            
            if (ret := self._router.match_route(path, method)):
                return ret[0](Request(addr, method, path, Request.parse_headers(headers_raw) if headers_raw else None, data if data else None), ret[1]).to_frame()

            else:
                return Response(204, headers = {"request-method": method, "request-path": path}).to_frame()

            return Response(101, headers = {"content-type": "descriptor"}, data = b"at end").to_frame()

    def serve(self, host: str, port: int):
        self._server.serve((host, port))

class Router:
    def __init__(self) -> None:
        self.handlers: dict[str, dict[str, typing.Callable[[Request, dict[str, str]], Response]]] = {}

        for method in METHODS:
            self.handlers[method] = {}

    def route(self, route_descriptor: str, methods: list[str] | None = None):
        def decorator(func: typing.Callable[[Request, dict[str, str]], Response]):
            methods_ = methods or ["GET"]

            for method in methods_:
                if method not in METHODS:
                    raise Exception(f"Unknown method {method!r}")

                self.handlers[method][route_descriptor] = func
            
            return func

        return decorator

    def match_route(self, route_descriptor: str, method: str) -> tuple[typing.Callable[[Request, dict[str, str]], Response], dict[str, str]] | None:
        if method not in METHODS:
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



import time, os, hashlib

sv = QSTP_Server()

@sv.route("/")
def index(rq: Request, _) -> Response:
    print(rq)

    resp = Response(200, headers = {"origin-method": rq.method}, data = b"test data")

    print(resp)

    return resp

@sv.route("/time_test")
def time_test(rq: Request, _) -> Response:
    if rq.data:
        time.sleep(int(rq.data))
    
    else:
        time.sleep(1)

    return Response(200)

@sv.route("/echo_body")
def echo(rq: Request, _) -> Response:
    return Response(200, data = rq.data)

@sv.route("/argtest/<arg1>")
def argtest(rq: Request, args: dict[str, str]) -> Response:
    print(args)

    return Response(200, data = str(args).encode())

@sv.route("/upload", methods = ["POST"])
def upload(rq: Request, _) -> Response:
    print(f"Headers: {rq.headers}")

    if not rq.headers:
        return Response(201, data = b"Need headers!")

    if not (filename := rq.headers.get("filename")):
        return Response(201, data = b"Need filename header!")
    
    if not (content_len := rq.headers.get("content-length")):
        return Response(201, data = b"Need content-length header!")
    
    if not (content_hash := rq.headers.get("content-hash")):
        return Response(201, data = b"Need content-hash header!")

    if not (content := rq.data):
        return Response(201, data = b"Need file content!")
    
    file_len = len(content)
    file_hash = hashlib.sha256(content).hexdigest()

    print(f"data lengths match: {file_len == int(content_len)}")
    print(f"data hashes match: {file_hash == content_hash}")
    
    with open(f"{os.getcwd()}/filetest/SERVER_OUTPUT__{filename}", "wb") as f:
        f.write(content)

    return Response(200)

sv.serve("localhost", 8080)