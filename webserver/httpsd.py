from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
from socketserver import ThreadingMixIn
from ssl import wrap_socket


class ThreadedHTTPSServer(ThreadingMixIn, HTTPServer):
    def __init__(self, certfile, cache, *args, **kwds):
        super().__init__(*args, **kwds)
        self.certfile = certfile
        self.cache = cache

    def server_bind(self):
        super().server_bind()
        self.socket = wrap_socket(self.socket,
                                  server_side=True,
                                  certfile=self.certfile,
                                  do_handshake_on_connect=False)

    def get_request(self):
        socket, addr = super().get_request()
        socket.do_handshake()
        return socket, addr


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pass