from http.server import HTTPServer, CGIHTTPRequestHandler
from socketserver import ThreadingMixIn
from ssl import wrap_socket
from typing import Mapping


class ThreadedHTTPSServer(ThreadingMixIn, HTTPServer):
    """An HTTPS server class which creates a thread for each client."""

    def __init__(self, certfile: str, keyfile: str, *args, **kwds):
        self.certfile = certfile
        self.keyfile = keyfile
        super().__init__(*args, **kwds)

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


def make_server(host: str,
                port: int,
                certificate: str,
                private_key: str,
                routes: Mapping[str, str]) -> ThreadedHTTPSServer:
    """Creates an HTTPS server.

    Arguments:
    host -- The IPv4 address or hostname to bind to.
    port -- The integer port to bind to.
    certificate -- The path to the certificate file.
    private_key -- The path to the private_key file.
    routes -- A mapping of pretty urls to file names.
    """
    PrettyURLRequestHandler.routes = routes
    return ThreadedHTTPSServer(certificate,
                               private_key,
                               (host, port),
                               PrettyURLRequestHandler)