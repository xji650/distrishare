import os
import shutil
import tempfile
import socket
import time

import pytest

from core.transfer import (
    start_file_server,
    remote_file_exists,
    download_file
)
from utils.config import SHARED_FOLDER, DOWNLOAD_FOLDER

@pytest.fixture(autouse=True)
def preparar_carpetas(tmp_path, monkeypatch):
    """
    Fixture que:
    - Redefine SHARED_FOLDER y DOWNLOAD_FOLDER a rutas temporales.
    - Se asegura de que esas carpetas estén creadas y vacías.
    """
    carpeta_shared = tmp_path / "shared_files_test"
    carpeta_downloads = tmp_path / "downloads_test"
    carpeta_shared.mkdir()
    carpeta_downloads.mkdir()

    # Parcheamos las variables de utils.config
    import utils.config as config_mod
    monkeypatch.setattr(config_mod, 'SHARED_FOLDER', str(carpeta_shared))
    monkeypatch.setattr(config_mod, 'DOWNLOAD_FOLDER', str(carpeta_downloads))

    yield  # tras el test, pytest borrará tmp_path entero

def test_remote_file_exists_y_download_file(tmp_path):
    """
    - Crea un archivo de prueba en SHARED_FOLDER.
    - Levanta un servidor TCP con start_file_server().
    - Verifica que remote_file_exists() detecta la presencia.
    - Llama a download_file() y comprueba que el archivo acaba en DOWNLOAD_FOLDER.
    """
    # 1. Crear archivo en el shared folder temporal
    nombre = "fichero_prueba.txt"
    contenido = b"Datos de prueba para transferencia."
    ruta_origen = os.path.join(SHARED_FOLDER, nombre)
    with open(ruta_origen, "wb") as f:
        f.write(contenido)

    # 2. Levantar servidor TCP en localhost con un puerto libre, por ejemplo 9100
    puerto_prueba = 9100
    start_file_server('127.0.0.1', puerto_prueba)

    # Dar un breve tiempo para que el servidor se inicialice
    time.sleep(0.1)

    # 3. remote_file_exists debe retornar True para el nombre correcto
    assert remote_file_exists('127.0.0.1', puerto_prueba, nombre) is True

    # 4. remote_file_exists con un nombre que no existe debe retornar False
    assert remote_file_exists('127.0.0.1', puerto_prueba, "no_existe.txt") is False

    # 5. download_file: descarga el archivo al DOWNLOAD_FOLDER
    download_file('127.0.0.1', puerto_prueba, nombre)

    ruta_descargado = os.path.join(DOWNLOAD_FOLDER, nombre)
    # El fichero debe haberse creado y tener el mismo contenido
    assert os.path.isfile(ruta_descargado)
    assert open(ruta_descargado, "rb").read() == contenido

def test_remote_file_exists_fuera_de_servidor():
    """
    Si no hay ningún servidor escuchando en esa ip:puerto, remota_file_exists devuelve False.
    """
    puerto_libre = 9999  # asumimos que no hay nada escuchando aquí
    assert remote_file_exists('127.0.0.1', puerto_libre, "cualquier.txt") is False
