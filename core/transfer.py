# core/transfer.py

import socket
import threading
import os
import json
from utils.config import SHARED_SECRET
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
    Solo acepta peticiones si el secreto es correcto.
    """
    try:
        data = conn.recv(4096)
        if not data:
            conn.close()
            return

        # Intenta cargar como JSON
        try:
            msg = json.loads(data.decode())
            secret = msg.get("secret")
            if secret != SHARED_SECRET:
                conn.sendall("ERROR: Autentication faild.".encode())
                conn.close()
                return
            # --- Caso 1: búsqueda de fichero ---
            if msg.get("type") == "search":
                filename = msg.get("filename", "")
                filepath = os.path.join(SHARED_FOLDER, filename)
                if os.path.isfile(filepath):
                    conn.sendall(FOUND.encode())
                    debug(f"Respondí FOUND para '{filename}'")
                else:
                    conn.sendall(NOT_FOUND.encode())
                    debug(f"Respondí NOT_FOUND para '{filename}'")
                conn.close()
                return
            # --- Caso 2: descarga de fichero ---
            if msg.get("type") == "download":
                filename = msg.get("filename", "")
                filepath = os.path.join(SHARED_FOLDER, filename)
                if not os.path.isfile(filepath):
                    conn.sendall(f"ERROR: File not found.".encode())
                    conn.close()
                    return
                with open(filepath, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        conn.sendall(chunk)
                debug(f"Transferencia completada de '{filename}'")
                conn.close()
                return
            # Si no reconoce el tipo
            conn.sendall(f"ERROR: Mensaje malformado o tipo desconocido.".encode())
            conn.close()
            return
        except Exception:
            # Si no es JSON válido, responde error
            conn.sendall("ERROR: Formato de mensaje inválido. Se requiere JSON.".encode())
            conn.close()
            return

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
        # Enviar mensaje como JSON que incluya el secreto
        payload = json.dumps({"type": "search", "filename": filename, "secret": SHARED_SECRET})
        sock.sendall(payload.encode())

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
        payload = json.dumps({"type": "download", "filename": filename, "secret": SHARED_SECRET})
        sock.sendall(payload.encode())


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
