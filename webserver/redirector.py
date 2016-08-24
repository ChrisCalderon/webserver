from http.server import BaseHTTPRequestHandler
from .interruptable import InterruptableServer

class RedirectHandler(BaseHTTPRequestHandler):
    """Just redirects to https."""
    host = None  # type: str

    def __getattr__(self, item):
        if item.startswith('do_'):
            return self._redirect

    def _redirect(self):
        new_location = 'https://' + self.host + self.path
        self.send_code(301)
        self.send_header('Location', new_location)
        self.send_header('Connection', 'close')


def make_redirector(host: str):
    """Starts an HTTP server which redirects to an HTTPS host.

    Argument:
    host -- the host to redirect to.
    """
    RedirectHandler.host = host
    httpd = InterruptableServer(('0.0.0.0', 80), RedirectHandler)
    return httpd
