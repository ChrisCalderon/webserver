from http.server import HTTPServer
from socketserver import ThreadingMixIn
import threading


class InterruptableServer(ThreadingMixIn, HTTPServer):
    def __init__(self, *args, **kwds):
        self._server_thread = None  # type: threading.Thread
        super().__init__(*args, **kwds)

    def serve_forever(self, poll_interval=0.5):
        self._server_thread = threading.Thread(target=super().serve_forever, args=(poll_interval,))
        self._server_thread.start()

    def join(self):
        self._server_thread.join()
