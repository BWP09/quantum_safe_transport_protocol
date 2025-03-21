import typing
import QSTP_server, QSTP_client, QSTP

class QSTP_ReverseProxy:
    def __init__(self, debug: bool = False) -> None:
        self._server = QSTP_server.QSTP_Server()
        self._debug = debug

    def serve(self, address: tuple[str, int]):
        @self._server.handle_data
        def _data_handler(rq: QSTP.Request) -> QSTP.Response:
            if self._debug:
                print(f" -- START LOG -- \nRequest from {rq.address}")

            if rq.headers is None or (host := rq.headers.get("Host")) is None:
                if self._debug:
                    print("Response 301, no Host specified")

                return QSTP.Response(301)

            rq.headers["Proxied-For"] = f"{rq.address[0]}:{rq.address[1]}"
            
            if (upstream := self.route_table.get(host)) is None:
                if (fallback := self.route_table.get("FALLBACK")) is None:
                    if self._debug:
                        print("Response 302, Host not found in route table and FALLBACK not defined")

                    return QSTP.Response(302)
                
                if self._debug:
                    print("Using FALLBACK address")

                rq.address = ((addr := fallback["location"].split(":"))[0], int(addr[1]))

            else:
                rq.address = ((addr := upstream["location"].split(":"))[0], int(addr[1]))

                if self._debug:
                    print(f"Using Upstream address {addr}")

            resp = QSTP_client.QSTP_Client().request_obj(rq)

            if self._debug:
                print(f"Response code: {resp.status_code}")

            if resp.status_code == 1:
                if self._debug:
                    print("Connection refused... trying FALLBACK")

                if (fallback := self.route_table.get("FALLBACK")) is not None:
                    rq.address = ((addr := fallback["location"].split(":"))[0], int(addr[1]))

                    resp = QSTP_client.QSTP_Client().request_obj(rq)

            if self._debug:
                print(f"Final Response code: {resp.status_code}")

            return resp

        self._server.serve(address)

    def close(self):
        self._server.close()

    def set_routing(self, route_table: dict[str, dict[str, str]]):
        self.route_table = route_table

if __name__ == "__main__":
    reverse_proxy = QSTP_ReverseProxy(debug = True)

    reverse_proxy.set_routing({
        "server1.com": {
            "location": "localhost:8081",
        },

        "server2.com": {
            "location": "localhost:8082",
        },

        "FALLBACK": {
            "location": "localhost:8081"
        }
    })

    reverse_proxy.serve(("0.0.0.0", 8080))