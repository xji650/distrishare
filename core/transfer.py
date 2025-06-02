# core/transfer.py

import socket
import threading
import os
from network.protocol import SEARCH_PREFIX, FOUND, NOT_FOUND
from utils.config import SHARED_FOLDER, DOWNLOAD_FOLDER
from utils.logger import info, error, debug

def ensure_folders():
    """
    Crea shared_files/ y downloads/ si no existen.
    """
    if not os.path.isdir(SHARED_FOLDER):
        os.makedirs(SHARED_FOLDER)
    if not os.path.isdir(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

def handle_client(conn: socket.socket):
    """
    Handler que se ejecuta en un hilo nuevo para cada conexión entrante.
    1) Si recibe 'SEARCH:<filename>', responde FOUND/NOT_FOUND
    2) Si recibe '<filename>' a secas, interpreta descarga:
       Envía el contenido binario si existe o 'ERROR: File not found.'
    """
    try:
        data = conn.recv(4096)
        if not data:
            conn.close()
            return

        message = data.decode()
        debug(f"Cliente conectó con mensaje: {message}")

        # --- Caso 1: búsqueda de fichero ---
        if message.startswith(SEARCH_PREFIX):
            filename = message[len(SEARCH_PREFIX):]
            filepath = os.path.join(SHARED_FOLDER, filename)
            if os.path.isfile(filepath):
                conn.sendall(FOUND.encode())
                debug(f"Respondí FOUND para '{filename}'")
            else:
                conn.sendall(NOT_FOUND.encode())
                debug(f"Respondí NOT_FOUND para '{filename}'")
            conn.close()
            return

        # --- Caso 2: solicitud de descarga ---
        filename = message.strip()
        filepath = os.path.join(SHARED_FOLDER, filename)
        if not os.path.isfile(filepath):
            conn.sendall(f"ERROR: File not found.".encode())
            conn.close()
            return

        # Envía el fichero en bloques de 4096 bytes
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                conn.sendall(chunk)

        debug(f"Transferencia completada de '{filename}'")
        conn.close()

    except Exception as e:
        error(f"Excepción en handle_client: {e}")
        conn.close()

def start_file_server(host: str, port: int):
    """
    Lanza un hilo en background que escucha en (host, port). Para cada
    nueva conexión, lanza handle_client() en un hilo nuevo.
    """
    ensure_folders()

    def server_loop():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.listen(5)
            info(f"[SERVIDOR P2P] Escuchando en {host}:{port}")
            while True:
                conn, addr = sock.accept()
                debug(f"Nueva conexión entrante desde {addr}")
                threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
        except Exception as e:
            error(f"Error en start_file_server: {e}")

    threading.Thread(target=server_loop, daemon=True).start()

def remote_file_exists(ip: str, port: int, filename: str) -> bool:
    """
    Realiza una conexión TCP a (ip, port) y envía "SEARCH:<filename>".
    Si recibe "FOUND", retorna True; si recibe "NOT_FOUND" o error, False.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 segundos de timeout
        sock.connect((ip, port))
        sock.sendall(f"{SEARCH_PREFIX}{filename}".encode())

        data = sock.recv(1024).decode()
        sock.close()
        debug(f"remote_file_exists recibió '{data}' de {ip}:{port}")
        return data == FOUND
    except Exception as e:
        debug(f"remote_file_exists error: {e}")
        return False

def download_file(ip: str, port: int, filename: str):
    """
    Conecta a (ip, port) y envía simplemente el nombre del fichero a descargar.
    Si existe, guarda el contenido en downloads/<filename>. Si no, muestra error.
    """
    ensure_folders()
    destino = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        sock.sendall(filename.encode())

        with open(destino, 'wb') as f:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                # Si viene un mensaje de error:
                if chunk.startswith(b"ERROR"):
                    msg = chunk.decode()
                    error(f"Error remoto: {msg}")
                    f.close()
                    os.remove(destino)
                    sock.close()
                    return
                f.write(chunk)

        sock.close()
        info(f"Descargado '{filename}' desde {ip}:{port} → {destino}")
    except Exception as e:
        error(f"Error en download_file: {e}")
        # Si hubo algún archivo parcial, lo borramos:
        if os.path.isfile(destino):
            os.remove(destino)
