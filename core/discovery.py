# core/discovery.py

import socket
import json
from utils.config import BOOTSTRAP_IP, BOOTSTRAP_PORT
from utils.logger import info, error

def register_with_bootstrap(my_ip: str, my_port: int) -> list:
    """
    Envía al bootstrap un mensaje de registro con (ip, port).
    Recibe y retorna la lista completa de nodos registrados.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((BOOTSTRAP_IP, BOOTSTRAP_PORT))
        payload = {'type': 'register', 'ip': my_ip, 'port': my_port}
        message = json.dumps(payload).encode()
        s.sendall(message)

        data = s.recv(4096)
        response = json.loads(data.decode())
        s.close()
        info(f"Registrado en Bootstrap: {response.get('nodes', [])}")
        return response.get('nodes', [])
    except Exception as e:
        error(f"Error al conectar con Bootstrap: {e}")
        return []
