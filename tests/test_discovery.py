# tests/test_discovery.py

import socket
import threading
import json
import time

import pytest

from core.discovery import register_with_bootstrap

IP_LOCAL = '127.0.0.1'
PUERTO_PRUEBA = 8500

@pytest.fixture
def servidor_bootstrap_falso(monkeypatch):
    """
    Arranca un servidor TCP falso en IP_LOCAL:PUERTO_PRUEBA que simula al bootstrap real.
    Cada vez que recibe un registro, devuelve una lista fija de nodos:
      [('127.0.0.1', 9001), ('127.0.0.1', 9002)].
    Además parchea las variables internas de core.discovery para que apunten a este servidor.
    """
    nodos_para_devolver = {'nodes': [("127.0.0.1", 9001), ("127.0.0.1", 9002)]}

    def handle_client(conn, addr):
        try:
            data = conn.recv(4096).decode()
            _ = json.loads(data)  # no es necesario validar el contenido
            respuesta = json.dumps(nodos_para_devolver).encode()
            conn.sendall(respuesta)
        except Exception:
            pass
        finally:
            conn.close()

    def server_loop():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((IP_LOCAL, PUERTO_PRUEBA))
        sock.listen(5)
        while True:
            conn, addr = sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

    # Parcheamos aquí las constantes dentro del módulo core.discovery:
    import core.discovery as disc_mod
    monkeypatch.setattr(disc_mod, 'BOOTSTRAP_IP', IP_LOCAL)
    monkeypatch.setattr(disc_mod, 'BOOTSTRAP_PORT', PUERTO_PRUEBA)

    # Arrancamos el servidor en un hilo daemon
    thread = threading.Thread(target=server_loop, daemon=True)
    thread.start()

    # Esperamos un instante para que el servidor comience a escuchar
    time.sleep(0.1)

    yield nodos_para_devolver['nodes']

    # No es necesario detener explícitamente el hilo porque es daemon.
    # Morirá cuando termine pytest.


def test_register_with_bootstrap_apunta_al_server_falso(servidor_bootstrap_falso):
    """
    Llamamos a register_with_bootstrap y comprobamos que recibe la lista ficticia
    desde el servidor falso.
    """
    resultado = register_with_bootstrap('127.0.0.1', 9001)
    # Convertimos cada elemento a tupla para comparar correctamente
    resultado_tuplas = [tuple(x) for x in resultado]

    assert isinstance(resultado, list)
    assert ("127.0.0.1", 9001) in resultado_tuplas
    assert ("127.0.0.1", 9002) in resultado_tuplas

