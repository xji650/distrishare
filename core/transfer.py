import socket
import threading
import os

SHARED_FOLDER = "shared_files"

def handle_client(conn):
    try:
        filename = conn.recv(1024).decode()
        filepath = os.path.join(SHARED_FOLDER, filename)

        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = f.read(1024)
                while data:
                    conn.sendall(data)
                    data = f.read(1024)
        else:
            conn.sendall(b"ERROR: File not found.")
    finally:
        conn.close()

def start_file_server(host='0.0.0.0', port=9000):
    def server():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print(f"[SERVIDOR] Escoltant per enviar fitxers a {host}:{port}")
            while True:
                conn, _ = s.accept()
                threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
    threading.Thread(target=server, daemon=True).start()

def download_file(ip, port, filename):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.sendall(filename.encode())

            with open(os.path.join(SHARED_FOLDER, filename), 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    if b"ERROR" in data:
                        print("Fitxer no trobat al node remot.")
                        return
                    f.write(data)

        print(f"[DESCÀRREGA] Fitxer {filename} descarregat correctament.")
    except Exception as e:
        print(f"Error en la descàrrega: {e}")
