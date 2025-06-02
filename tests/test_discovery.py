import socket
import threading
import json
import time

import pytest

from core.discovery import register_with_bootstrap

# Puerto de prueba para el “bootstrap” ficticio:
PUERTO_PRUEBA = 8500
IP_LOCAL = '127.0.0.1'

@pytest.fixture(scope="module")
def servidor_bootstrap_falso():
    """
    Inicia un servidor TCP ficticio antes de los tests y lo cierra al final.
    El servidor simula el comportamiento: al recibir JSON con type='register',
    responde con {'nodes': [("127.0.0.1", 9001), ("127.0.0.1", 9002)]}.
    """
    resultados_para_devolver = {
        'nodes': [("127.0.0.1", 9001), ("127.0.0.1", 9002)]
    }

    def handle_client(conn, addr):
        data = conn.recv(1024).decode()
        payload = json.loads(data)
        # Podemos verificar que payload['type']=='register'
        response = json.dumps(resultados_para_devolver).encode()
        conn.sendall(response)
        conn.close()

    def server_loop():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((IP_LOCAL, PUERTO_PRUEBA))
        sock.listen(5)
        while not stop_event.is_set():
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        sock.close()

    stop_event = threading.Event()
    thread = threading.Thread(target=server_loop, daemon=True)
    # Para que sock.accept() no bloquee eternamente, configuramos timeout
    def set_timeout():
        sock_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_temp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_temp.bind((IP_LOCAL, PUERTO_PRUEBA))
        sock_temp.listen(1)
        sock_temp.settimeout(0.5)
        sock_temp.close()
    # Iniciar el servidor
    thread.start()
    # Dar un breve lapso para que empiece a escuchar
    time.sleep(0.1)

    yield resultados_para_devolver['nodes']

    # Tras los tests, detener el servidor
    stop_event.set()
    thread.join(timeout=1)

def test_register_with_bootstrap_apunta_al_server_falso(monkeypatch, servidor_bootstrap_falso):
    """
    Cambiamos temporalmente los valores BOOTSTRAP_IP y BOOTSTRAP_PORT para que apunte al servidor ficticio.
    """
    # Sobrescribimos la configuración de bootstrap en tiempo de ejecución
    import utils.config as config_mod
    monkeypatch.setattr(config_mod, 'BOOTSTRAP_IP', IP_LOCAL)
    monkeypatch.setattr(config_mod, 'BOOTSTRAP_PORT', PUERTO_PRUEBA)

    # Ahora llamamos register_with_bootstrap
    resultado = register_with_bootstrap('127.0.0.1', 9001)

    # Debe coincidir con la lista que el servidor ficticio devolvió
    assert isinstance(resultado, list)
    assert ("127.0.0.1", 9001) in resultado
    assert ("127.0.0.1", 9002) in resultado
    # El peer se registra a sí mismo con port=9001, así que "127.0.0.1:9001" puede estar repetido
