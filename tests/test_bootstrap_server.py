import socket
import threading
import json
import time

import pytest

from network.bootstrap_server import start_server

IP_LOCAL = '127.0.0.1'
PUERTO_BOOTSTRAP = 8600  # Puerto para este test

@pytest.fixture(scope="module")
def servidor_bootstrap_real():
    """
    Levanta el bootstrap real en un hilo antes de los tests y lo detiene al terminar.
    """
    def run_server():
        start_server(host=IP_LOCAL, port=PUERTO_BOOTSTRAP)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    # Esperamos un momento a que arranque
    time.sleep(0.1)
    yield
    # Como start_server() es un bucle infinito, 
    # no podemos “detenerlo limpiamente” a menos que reestructuremos el servidor.
    # Con daemon=True, al terminar pytest el proceso se cierra y el thread muere.
    # Por tanto, no hacemos nada especial aquí.

def test_registrar_varios_peers(servidor_bootstrap_real):
    """
    Conecta varios “clientes” simultáneamente, registrándose en el bootstrap
    y comprueba que la lista que devuelve contiene a todos.
    """
    nodos_respuesta = set()

    for puerto in (9010, 9020, 9030):
        # 1. Crear socket cliente
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((IP_LOCAL, PUERTO_BOOTSTRAP))
        payload = {'type': 'register', 'ip': IP_LOCAL, 'port': puerto}
        s.sendall(json.dumps(payload).encode())

        data = s.recv(4096)
        respuesta = json.loads(data.decode())
        s.close()

        # Extraemos la lista de nodos que devuelve el bootstrap
        for ip, p in respuesta.get('nodes', []):
            nodos_respuesta.add((ip, p))

    # Tras registrar 3 peers, nodos_respuesta debe contener al menos 3 pares distintos
    assert (IP_LOCAL, 9010) in nodos_respuesta
    assert (IP_LOCAL, 9020) in nodos_respuesta
    assert (IP_LOCAL, 9030) in nodos_respuesta
