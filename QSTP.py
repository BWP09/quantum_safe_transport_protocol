import typing

VERSION = "QSTP/1"

status_codes = {
      1: "CONNECTION REFUSED",
    100: "SERVER OK",
    101: "SERVER ERROR",
    200: "OK",
    201: "MALFORMED",
    202: "UNKNOWN VERSION",
    203: "UNKNOWN METHOD",
    204: "UNKNOWN PATH",
    205: "UNAUTHENTICATED",
    206: "UNAUTHORIZED",
    300: "OK",
    301: "INCOMPLETE",
    302: "UNKNOWN HOST",
}

METHODS = {
    "GET",
    "POST",
    "DELETE",
    "PATCH",
}

def parse_headers(headers: str) -> dict[str, str]:
        headers_out = {}

        for line in headers.split("\n"):
            k, v = line.split(":", 1)

            headers_out[k.strip()] = v.strip()

        return headers_out

class Request:
    def __init__(self, address: tuple[str, int], method: str, path: str, headers: dict[str, str] | None = None, data: bytes | None = None) -> None:
        if method not in METHODS:
            raise ValueError(f"{method} is not a method")

        self.address = address
        self.method = method
        self.path = path
        self.headers = headers
        self.data = data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(address = {self.address}, method = {self.method!r}, path = {self.path!r}{f", headers = {self.headers}" if self.headers else ""}{f", data = {self.data[:50]}{"..." if len(self.data) > 50 else ""}" if self.data else ""})"

    def to_frame(self) -> bytes:
        head = f"{VERSION} {self.method} {self.path}{("\n" + "\n".join(f"{k}: {v}" for k, v in self.headers.items())) if self.headers else ""}"

        return head.encode() + (b"\n\n" + self.data if self.data else b"")

    @staticmethod
    def from_frame(frame: bytes, address: tuple[str, int]) -> "Request | Response":
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
            return Response(201)

        version, method, path = info_line_split

        if version != VERSION:
            return Response(202)

        if method not in METHODS:
            return Response(203)

        return Request(address, method, path, parse_headers(headers_raw) if headers_raw else None, data if data else None)

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
        head = f"{VERSION} {self.status_code} {status_codes[self.status_code]}{("\n" + "\n".join(f"{k}: {v}" for k, v in self.headers.items())) if self.headers else ""}"

        return head.encode() + (b"\n\n" + self.data if self.data else b"")

    @staticmethod
    def from_frame(frame: bytes) -> "Response":
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
            raise ValueError("parsing failed at info line!")

        version, status_code, _ = info_line_split

        if version != VERSION:
            raise ValueError("incorrect version!")

        try:
            status_code = int(status_code)

        except ValueError:
            raise ValueError("invalid status code!")

        return Response(status_code, parse_headers(headers_raw) if headers_raw else None, data if data else None)