import typing

METHODS = {
    "GET",
    "POST",
    "DELETE",
    "PATCH",
}

class Router:
    def __init__(self) -> None:
        self.handlers: dict[str, dict[str, typing.Callable]] = {}

        for method in METHODS:
            self.handlers[method] = {}

    def route(self, route_descriptor: str, methods: list[str] | None = None):
        def decorator(func: typing.Callable[[str], str]):
            methods_ = methods or ["GET"]

            for method in methods_:
                if method not in METHODS:
                    raise Exception(f"Unknown method {method!r}")

                self.handlers[method][route_descriptor] = func
            
            return func

        return decorator

    def match_route(self, route_descriptor: str, method: str) -> typing.Callable | None:
        if method not in METHODS:
            raise Exception(f"Unknown method {method!r}")

        return self.handlers[method].get(route_descriptor)

def test1():
    router = Router()

    @router.route("/", methods = ["GET"])
    def index(string: str) -> str:
        return f"input: \"{string}\""

    @router.route("/data", methods = ["GET", "POST", "PATCH", "DELETE"])
    def data(string: str) -> str:
        return f"input: \"{string}\""

    @router.route("/test/<test_data>", methods = ["POST"])
    def test(string: str) -> str:
        return f"input: \"{string}\""

    tests = [
        ("/", "GET"),
        ("/data", "PATCH"),
        ("/test", "POST"),

        ("/", "POST"),
        ("/data", "GET"),
        ("/test", "GET"),
    ]

    for route, method in tests:
        print(router.match_route(route, method))

route_defined = "/test_before/<data>/test_after"
route_try_matching = "/test_before/data_test_123/test_after"


path_defined = []
path_try = {}

for part in route_defined.split("/"):
    print(part)

    if part.startswith("<") and part.endswith(">"):
        path_defined.append({"var": part[1:-1]})
    
    elif part:
        path_defined.append({"path": part})

print(path_defined)