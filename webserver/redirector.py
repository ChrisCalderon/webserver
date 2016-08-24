from http.server import BaseHTTPRequestHandler
from .interruptable import InterruptableServer

class RedirectHandler(BaseHTTPRequestHandler):
    """Just redirects to https."""
    host = None  # type: str

    def do_GET(self):
        new_location = 'https://' + self.host + self.path
        print('Redirecting HTTP request to', new_location)
        self.send_response(301)
        self.send_header('Location', new_location)
        self.send_header('Connection', 'close')

    do_HEAD = do_GET
    do_POST = do_GET


def make_redirector(host: str):
    """Starts an HTTP server which redirects to an HTTPS host.

    Argument:
    host -- the host to redirect to.
    """
    RedirectHandler.host = host
    httpd = InterruptableServer(('0.0.0.0', 80), RedirectHandler)
    return httpd
