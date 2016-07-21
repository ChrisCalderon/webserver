"""A Process subclass for managing access to files."""
import multiprocessing
import socket
import select
import hashlib
import json
import time
import os
import codecs
from typing import Tuple, List, Dict, Optional, Union, MutableSequence, T, _geqv
from collections import deque

Request = Dict[str, Union[str, List[str]]]
Address = Tuple[str, int]
MAX_CONNECTIONS = 255  # The max number of connections to accept at once


class Deque(deque, MutableSequence[T], extra=deque):
    """A typing-like type for use with function signatures using deque's."""
    def __new__(cls, *args, **kwds):
        if _geqv(cls, Deque):
            raise TypeError("Type Deque cannot be instantiated; "
                            "use deque() instead")
        return deque.__new__(cls, *args, **kwds)


def get_connections(listener: socket.socket,
                    timeout: int = 1,
                    max_connections: int = MAX_CONNECTIONS) -> Deque[socket.socket]:
    """Gets connections to a listening socket."""
    connections = deque()
    has_pending_connections = select.select([listener], [], [], timeout)[0]
    if has_pending_connections:
        for i in range(MAX_CONNECTIONS):
            try:
                connection = listener.accept()[0]
            except socket.error:
                break
            else:
                connections.append(connection)
    return connections


def full_recv(conn: socket.socket, n: int, max_tries: int = 100) -> bytearray:
    """Tries to recv n bytes from a connection."""
    payload = bytearray()
    tries = 0
    while len(payload) < n and tries < max_tries:
        remaining_amount = n - len(payload)
        try:
            data_chunk = conn.recv(remaining_amount)
        except socket.error:
            break
        payload.extend(data_chunk)
        tries += 1
    return payload


def recv_json(connection: socket.socket) -> Optional[Request]:
    """Reads a JSON request from a socket connection."""
    json_length = full_recv(connection, 4)
    if json_length is None or len(json_length) < 4:
        return
    json_length = int.from_bytes(json_length, byteorder='big')
    json_request = full_recv(connection, json_length)
    if json_request is None or len(json_request) < json_length:
        return
    return json.loads(json_request.decode('utf8'))


def is_valid_request(request: Optional[Request]) -> bool:
    return (request is not None and
            set(request) == {'method', 'params'} and
            isinstance(request['method'], str) and
            isinstance(request['params'], list) and
            all(isinstance(p, str) for p in request['params']))


class Cache(multiprocessing.Process):
    def __init__(self,
                 authkey: str,
                 bind_loc: Address,
                 static_dir: str,
                 file_poll_interval: int):
        super().__init__()
        self.address = bind_loc
        self.authkey = authkey
        self.static_dir = static_dir
        self.file_poll_interval = file_poll_interval

    def send_request(self, method: str, params: List[str]) -> str:
        connection = socket.create_connection(self.address)
        payload = json.dumps({'method': method, 'params': params}).encode('utf8')
        length = len(payload).to_bytes(4, 'big')
        try:
            connection.sendall(length + payload)
        except socket.error:
            return 'failure'
        status = full_recv(connection, 7)
        if len(status) != 7:
            return 'failure'
        return status.decode('utf8')

    def run(self):
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.setblocking(0)
        listener.bind(self.address)
        listener.listen()
        files = {}
        last_update_time = 0
        static_dir = self.static_dir
        running = True
        file_poll_interval = self.file_poll_interval

        def sendfile(filename: str, share_data: str):
            full_path = os.path.join(static_dir,
                                     os.path.normpath(filename))
            if not os.path.exists(full_path):
                return
            info = files.get(full_path, None)
            if info is None:
                with open(full_path)as f:
                    info = {'data': f.read(),
                            'mtime': os.stat(full_path).st_mtime}
                files[full_path] = info

            share_data = codecs.decode(share_data.encode(), 'hex')
            conn2 = socket.fromshare(share_data) # this is an http connection in a different process
            conn2.sendall(info['data'])
            conn2.close()

        while running:
            current_time = time.time()
            if (current_time - last_update_time) > file_poll_interval:
                for full_path in files:

            connections = get_connections(listener)
            while connections:
                conn = connections.popleft()
                request = recv_json(conn)
                status = b'failure'
                if is_valid_request(request):
                    method = request['method']
                    params = request['params']
                    if method == 'sendfile' and len(params) == 2:
                        try:
                            sendfile(*params)
                        except (IOError, socket.error, OSError) as exc:
                            print(exc)
                        else:
                            status = b'success'
                    if method == 'shutdown' and len(params) == 1:
                        auth_key = hashlib.sha256(params[0]).hexdigest()
                        if auth_key == self.authkey:
                            running = False
                            status = b'success'
                conn.sendall(status)
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()

                if not running:
                    break

            while connections:  # a shutdown call might leave open connections.
                conn = connections.popleft()
                conn.send(b'failure')
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()

        listener.shutdown(socket.SHUT_RDWR)
        listener.close()
        print('shutting down')












