import socket
import threading
import json

nodes = []

def handle_client(conn, addr):
    data = conn.recv(1024).decode()
    request = json.loads(data)
    if request['type'] == 'register':
        node = (request['ip'], request['port'])
        if node not in nodes:
            nodes.append(node)
        conn.sendall(json.dumps({'nodes': nodes}).encode())
    conn.close()

def start_server(host='0.0.0.0', port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Bootstrap server escoltant a {host}:{port}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
