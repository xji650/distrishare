# network/bootstrap_server.py

import socket
import threading
import json
from utils.logger import info, debug, error

# Lista global en memoria
nodes = []

def handle_client(conn: socket.socket, addr):
    """
    Maneja un peer que quiere registrarse.
    Recibe JSON con {'type':'register','ip':..., 'port':...}
    Añade a nodes si no existía y responde {'nodes': nodes}.
    """
    try:
        data = conn.recv(4096).decode()
        debug(f"[BOOTSTRAP] Mensaje de {addr}: {data}")
        request = json.loads(data)

        if request.get('type') == 'register':
            peer_info = (request.get('ip'), request.get('port'))
            if peer_info not in nodes:
                nodes.append(peer_info)
                info(f"[BOOTSTRAP] Registrado peer: {peer_info}")
            else:
                debug(f"[BOOTSTRAP] Peer ya existía: {peer_info}")
            response = {'nodes': nodes}
            conn.sendall(json.dumps(response).encode())
        else:
            error(f"[BOOTSTRAP] Tipo de mensaje desconocido: {request}")
    except Exception as e:
        error(f"[BOOTSTRAP] Excepción en handle_client: {e}")
    finally:
        conn.close()

def start_server(host: str = '0.0.0.0', port: int = 8000):
    """
    Inicia el servidor TCP que acepta registros de peers.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(5)
        info(f"[BOOTSTRAP] Servidor escuchando en {host}:{port}")
        while True:
            conn, addr = sock.accept()
            debug(f"[BOOTSTRAP] Conexión entrante desde {addr}")
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        error(f"[BOOTSTRAP] Error en start_server: {e}")

if __name__ == "__main__":
    start_server()
