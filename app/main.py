import socket
import threading


def handle_client(conn: socket.socket, addr):
    while True:
        data = conn.recv(1024).decode()
        print(f"data received: {data}")
        if not data:
            break
        conn.send("+PONG\r\n".encode())
    conn.close()


def main():
    while True:
        server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
        conn, addr = server_socket.accept()  # wait for client
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()


if __name__ == "__main__":
    main()
