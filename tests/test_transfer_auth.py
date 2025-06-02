import os
import time
import json
import socket
import pytest

from core.transfer import start_file_server
import core.transfer as transfer_mod
import utils.config as config_mod

@pytest.fixture(autouse=True)
def preparar_carpetas(tmp_path, monkeypatch):
    carpeta_shared = tmp_path / "shared_test"
    carpeta_downloads = tmp_path / "downloads_test"
    carpeta_shared.mkdir(parents=True, exist_ok=True)
    carpeta_downloads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(config_mod, 'SHARED_FOLDER', str(carpeta_shared))
    monkeypatch.setattr(config_mod, 'DOWNLOAD_FOLDER', str(carpeta_downloads))
    monkeypatch.setattr(transfer_mod, 'SHARED_FOLDER', str(carpeta_shared))
    monkeypatch.setattr(transfer_mod, 'DOWNLOAD_FOLDER', str(carpeta_downloads))

    yield

def test_search_con_secreto_correcto():
    """El peer responde FOUND si el secreto es correcto y el archivo existe."""
    from utils.config import SHARED_FOLDER, SHARED_SECRET
    nombre = "prueba.txt"
    with open(os.path.join(SHARED_FOLDER, nombre), "w") as f:
        f.write("abc")

    puerto = 9210
    start_file_server('127.0.0.1', puerto)
    time.sleep(0.1)

    payload = json.dumps({
        "type": "search",
        "filename": nombre,
        "secret": SHARED_SECRET
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', puerto))
    sock.sendall(payload.encode())
    respuesta = sock.recv(1024)
    sock.close()
    assert respuesta.decode() == "FOUND"

def test_search_con_secreto_incorrecto():
    """El peer rechaza la búsqueda si el secreto es incorrecto."""
    from utils.config import SHARED_SECRET, SHARED_FOLDER
    nombre = "nada.txt"
    with open(os.path.join(SHARED_FOLDER, nombre), "w") as f:
        f.write("nope")

    puerto = 9211
    start_file_server('127.0.0.1', puerto)
    time.sleep(0.1)

    payload = json.dumps({
        "type": "search",
        "filename": nombre,
        "secret": "SECRETO_MAL"
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', puerto))
    sock.sendall(payload.encode())
    respuesta = sock.recv(1024)
    sock.close()
    assert b"Autentication faild" in respuesta

def test_download_con_secreto_correcto(tmp_path):
    """Descarga exitosa solo si el secreto es correcto."""
    from utils.config import SHARED_SECRET, SHARED_FOLDER, DOWNLOAD_FOLDER
    nombre = "descarga.txt"
    contenido = b"contenido secreto"
    with open(os.path.join(SHARED_FOLDER, nombre), "wb") as f:
        f.write(contenido)

    puerto = 9212
    start_file_server('127.0.0.1', puerto)
    time.sleep(0.1)

    payload = json.dumps({
        "type": "download",
        "filename": nombre,
        "secret": SHARED_SECRET
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', puerto))
    sock.sendall(payload.encode())

    destino = os.path.join(DOWNLOAD_FOLDER, nombre)
    with open(destino, "wb") as f:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            f.write(chunk)
    sock.close()
    assert os.path.exists(destino)
    assert open(destino, "rb").read() == contenido

def test_download_con_secreto_incorrecto(tmp_path):
    """La descarga falla si el secreto es incorrecto."""
    from utils.config import SHARED_FOLDER, DOWNLOAD_FOLDER
    nombre = "descarga.txt"
    with open(os.path.join(SHARED_FOLDER, nombre), "w") as f:
        f.write("sin permiso")

    puerto = 9213
    start_file_server('127.0.0.1', puerto)
    time.sleep(0.1)

    payload = json.dumps({
        "type": "download",
        "filename": nombre,
        "secret": "NO_ES_EL_BUENO"
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', puerto))
    sock.sendall(payload.encode())
    respuesta = sock.recv(1024)
    sock.close()
    # No debe crearse ningún archivo descargado
    destino = os.path.join(DOWNLOAD_FOLDER, nombre)
    assert b"Autentication faild" in respuesta
    assert not os.path.exists(destino)
