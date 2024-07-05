import re
import socket
import threading


def process_ping(conn: socket.socket):
    conn.send("+PONG\r\n".encode())


def process_echo(conn: socket.socket, msg: str):
    conn.send(f"+{msg}\r\n".encode())


def resp_parser(conn: socket.socket, message: str):
    commands = message.split(sep="\r\n")
    amount_commands = int(commands[0][1:])
    pattern = r"[\$*][0-9]"
    commands = [re.sub(pattern, "", s).strip() for s in commands if re.sub(pattern, "", s).strip()]
    while commands:
        if commands[0] == "PING":
            process_ping(conn)
            commands = commands[1:]
        elif commands[0] == "ECHO":
            process_echo(conn, commands[1])
            commands = commands[2:]
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
