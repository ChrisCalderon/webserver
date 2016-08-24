from .interruptable import InterruptableServer
from http.server import CGIHTTPRequestHandler
from ssl import wrap_socket
from typing import Mapping


class ThreadedHTTPSServer(InterruptableServer):
    """An HTTPS server class which creates a thread for each client."""
    default_address = ('0.0.0.0', 443)

    def __init__(self, certfile: str, keyfile: str, *args, **kwds):
        self.certfile = certfile
        self.keyfile = keyfile
        super().__init__(self.default_address, *args, **kwds)

    def server_bind(self):
        super().server_bind()
        self.socket = wrap_socket(self.socket,
                                  server_side=True,
                                  certfile=self.certfile,
                                  keyfile=self.keyfile,
                                  do_handshake_on_connect=False)

    def get_request(self):
        socket, addr = super().get_request()
        socket.do_handshake()
        return socket, addr


class PrettyURLRequestHandler(CGIHTTPRequestHandler):
    """A handler class for pretty routing."""
    routes = None  # type: Mapping[str, str]

    def _pretty(self, do_meth):
        if self.path in self.routes:
            print('rerouting:', self.path, '->', self.routes[self.path])
            self.path = self.routes[self.path]
        do_meth()  # ;)

    def do_GET(self):
        self._pretty(super().do_GET)

    def do_HEAD(self):
        self._pretty(super().do_HEAD)

    def do_POST(self):
        self._pretty(super().do_POST)


def make_server(certificate: str,
                private_key: str,
                routes: Mapping[str, str]) -> ThreadedHTTPSServer:

    PrettyURLRequestHandler.routes = routes
    return ThreadedHTTPSServer(certificate, private_key,
                               PrettyURLRequestHandler)
