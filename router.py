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

    def match_route(self, route_descriptor: str, method: str) -> tuple[typing.Callable, dict[str, str]] | None:
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
        ("/test/data", "POST"),

        ("/", "POST"),
        ("/data", "GET"),
        ("/test", "GET"),
    ]

    for route, method in tests:
        print(router.match_route(route, method))

test1()

def match_route(defined_route_descriptor: str, test_route_descriptor: str) -> dict[str, str] | None:
    path_defined = []
    path_try = []

    for part in defined_route_descriptor.split("/"):
        if part.startswith("<") and part.endswith(">"):
            path_defined.append((1, part[1:-1]))
        
        elif part:
            path_defined.append((0, part))

    path_try = list(filter(lambda x: bool(x), test_route_descriptor.split("/")))

    if len(path_defined) != len(path_try):
        return
    
    variables = {}

    for defined, test in zip(path_defined, path_try):
        if defined[0] == 0 and defined[1] == test:
            continue
        
        elif defined[0] == 1:
            variables[defined[1]] = test

        else:
            return

    return variables

def test2():
    tests = [
        ("/test_before/<data>/test_after", "/test_before/data_test_123/test_after"),
        ("/users/<user>", "/users/bwp09"),
        ("/users/<user>/comment/<comment>", "/users/bwp09/comment/190283901283"),
        ("/test", "/test"),
        ("/post/<post_id>", "/post/01923890/likes"),
        ("/<one>/<two>/<three>", "/one/two/three/four"),
        ("/<test>", "/1238901283091283"),
        ("/test", "/test/123"),
    ]

    for i, (x, y) in enumerate(tests):
        print(f"{i} START")
        print(match_route(x, y))
        print(f"{i} END")