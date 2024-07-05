import re
import socket
import threading
import time
from collections.abc import MutableMapping


class TTLDict(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.ttl_store = dict()
        self.update(dict(*args, **kwargs))

    def _cleanup(self):
        current_time = time.time() * 1000
        expired_keys = [key for key, ttl in self.ttl_store.items() if ttl is not None and ttl < current_time]
        for key in expired_keys:
            del self.store[key]
            del self.ttl_store[key]

    def __getitem__(self, key):
        self._cleanup()
        return self.store[key]

    def __setitem__(self, key, value, ttl=None):
        self._cleanup()
        self.store[key] = value
        if ttl is not None:
            self.ttl_store[key] = time.time() * 1000 + ttl
        else:
            self.ttl_store[key] = None

    def __delitem__(self, key):
        del self.store[key]
        if key in self.ttl_store:
            del self.ttl_store[key]

    def __iter__(self):
        self._cleanup()
        return iter(self.store)

    def __len__(self):
        self._cleanup()
        return len(self.store)

    def __repr__(self):
        self._cleanup()
        return repr(self.store)

    def set(self, key, value, ttl=None):
        self.__setitem__(key, value, ttl)

    def get(self, key, default=None):
        self._cleanup()
        return self.store.get(key, default)


redis_store = TTLDict()


def process_ping(conn: socket.socket):
    conn.send("+PONG\r\n".encode())


def process_echo(conn: socket.socket, msg: str):
    conn.send(f"+{msg}\r\n".encode())


def process_set(conn: socket.socket, key: str, val: str, ttl: int = None):
    print(f"setting key {key} to value {val} with ttl {ttl}")
    redis_store.set(key, val, ttl)
    conn.send("+OK\r\n".encode())


def process_get(conn: socket.socket, key: str):
    response = redis_store.get(key)
    if response:
        conn.send(f"${len(response)}\r\n{response}\r\n".encode())
    else:
        conn.send("$-1\r\n".encode())


def resp_parser(conn: socket.socket, message: str):
    commands = message.split(sep="\r\n")
    amount_commands = int(commands[0][1:])
    pattern = r"[\$*][0-9]*"
    commands = [re.sub(pattern, "", s).strip() for s in commands if re.sub(pattern, "", s).strip()]
    print(f"commands are {commands}")
    while commands:
        cmd = commands[0].lower()
        if cmd == "ping":
            process_ping(conn)
            commands = commands[1:]
        elif cmd == "echo":
            process_echo(conn, commands[1])
            commands = commands[2:]
        elif cmd == "get":
            process_get(conn, commands[1])
            commands = commands[2:]
        elif cmd == "set":
            if len(commands) > 3 and commands[3].lower() == "px":
                process_set(conn, commands[1], commands[2], int(commands[4]))
                commands = commands[5:]
            else:
                process_set(conn, commands[1], commands[2])
                commands = commands[3:]
        else:
            commands = commands[1:]


def handle_client(conn: socket.socket, addr):
    while True:
        message = conn.recv(1024).decode()
        if not message:
            break
        resp_parser(conn, message)
    conn.close()


def main():
    while True:
        server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
        conn, addr = server_socket.accept()  # wait for client
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()


if __name__ == "__main__":
    main()
