from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from multiprocessing import Process


class ThreadedHTTPRedirector(ThreadingMixIn, HTTPServer):
    """A threaded HTTP server that's only for redirection."""
    pass


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


class Redirector(Process):
    def __init__(self, host):
        self.host = host

    def run(self):
        RedirectHandler.host = self.host
        server = ThreadedHTTPRedirector(('0.0.0.0', 80),
                                        RedirectHandler)


def make_redirector(host: str):
    Redirector.host = host
    httpd = ThreadedHTTPRedirector(('0.0.0.0', 80),
                                   Redirector)

    return httpd
