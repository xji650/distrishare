# tests/test_transfer.py

import os
import time

import pytest

from core.transfer import start_file_server, remote_file_exists, download_file
import utils.config as config_mod
import core.transfer as transfer_mod  # para parchear SHARED_FOLDER interno

@pytest.fixture(autouse=True)
def preparar_carpetas(tmp_path, monkeypatch):
    """
    Fixture que redefine SHARED_FOLDER y DOWNLOAD_FOLDER a rutas bajo tmp_path,
    y además parcha la constante interna transfer_mod.SHARED_FOLDER para que
    el servidor de archivos use la misma carpeta.
    """
    # Creamos dos subdirectorios dentro de tmp_path
    carpeta_shared = tmp_path / "shared_test"
    carpeta_downloads = tmp_path / "downloads_test"
    carpeta_shared.mkdir(parents=True, exist_ok=True)
    carpeta_downloads.mkdir(parents=True, exist_ok=True)

    # Parcheamos utils.config
    monkeypatch.setattr(config_mod, 'SHARED_FOLDER', str(carpeta_shared))
    monkeypatch.setattr(config_mod, 'DOWNLOAD_FOLDER', str(carpeta_downloads))

    # Parcheamos la constante interna de core.transfer para que use el mismo SHARED_FOLDER
    monkeypatch.setattr(transfer_mod, 'SHARED_FOLDER', str(carpeta_shared))
    monkeypatch.setattr(transfer_mod, 'DOWNLOAD_FOLDER', str(carpeta_downloads))

    yield  # pytest borrará tmp_path al final automáticamente


def test_remote_file_exists_y_download_file(preparar_carpetas):
    """
    - Crea un archivo de prueba en SHARED_FOLDER (el parcheado).
    - Levanta un servidor TCP con start_file_server().
    - Verifica que remote_file_exists() lo detecta.
    - Llama a download_file() y comprueba que el archivo acaba en DOWNLOAD_FOLDER.
    """
    from utils.config import SHARED_FOLDER, DOWNLOAD_FOLDER

    nombre = "fichero_prueba.txt"
    contenido = b"Datos de prueba para transferencia."
    ruta_origen = os.path.join(SHARED_FOLDER, nombre)

    # Aseguramos que la carpeta existe (ya la creó la fixture)
    os.makedirs(SHARED_FOLDER, exist_ok=True)

    # Creamos el fichero de prueba
    with open(ruta_origen, "wb") as f:
        f.write(contenido)

    # Arrancamos el servidor TCP en localhost con un puerto fijo (ej. 9100)
    puerto_prueba = 9100
    start_file_server('127.0.0.1', puerto_prueba)

    # Pequeña pausa para que el servidor ya esté en listen()
    time.sleep(0.1)

    # remote_file_exists debe retornar True para el fichero creado
    assert remote_file_exists('127.0.0.1', puerto_prueba, nombre) is True

    # remote_file_exists con un nombre inexistente → False
    assert remote_file_exists('127.0.0.1', puerto_prueba, "no_existe.txt") is False

    # Ejecutamos download_file para bajar el fichero a DOWNLOAD_FOLDER
    download_file('127.0.0.1', puerto_prueba, nombre)

    ruta_descargado = os.path.join(DOWNLOAD_FOLDER, nombre)
    # Comprobamos que el fichero existe y su contenido coincide
    assert os.path.isfile(ruta_descargado)
    with open(ruta_descargado, "rb") as f:
        assert f.read() == contenido


def test_remote_file_exists_fuera_de_servidor():
    """
    Si no hay servidor en IP:puerto, remote_file_exists() devuelve False.
    """
    puerto_libre = 9999  # suponemos que no hay nada escuchando aquí
    assert remote_file_exists('127.0.0.1', puerto_libre, "cualquier.txt") is False
