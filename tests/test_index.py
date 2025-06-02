import os
import shutil
import tempfile

import pytest

from core.index import list_shared_files, add_file
from utils.config import SHARED_FOLDER

@pytest.fixture(autouse=True)
def limpiar_shared_folder():
    """
    Fixture que se ejecuta antes y después de cada test:
    - Se asegura de que SHARED_FOLDER existe y está vacío.
    - Al finalizar, borra todo su contenido.
    """
    # Antes del test: crea la carpeta si no existe y la vacía
    if os.path.isdir(SHARED_FOLDER):
        shutil.rmtree(SHARED_FOLDER)
    os.makedirs(SHARED_FOLDER)

    yield

    # Después del test: limpiar
    if os.path.isdir(SHARED_FOLDER):
        shutil.rmtree(SHARED_FOLDER)

def test_list_shared_empty():
    """
    Cuando SHARED_FOLDER está vacío, list_shared_files() debe retornar lista vacía.
    """
    archivos = list_shared_files()
    assert archivos == []

def test_add_and_list_shared_file(tmp_path):
    """
    Crea un fichero temporal en tmp_path, lo pasa a add_file(),
    y verifica que aparece en SHARED_FOLDER y en list_shared_files().
    """
    # 1. Crear un fichero de prueba
    origen = tmp_path / "prueba.txt"
    contenido = b"Hola DistriShare!"
    origen.write_bytes(contenido)

    # 2. Llamar a add_file(ruta)
    add_file(str(origen))

    # 3. El fichero debe existir en SHARED_FOLDER
    nombre = "prueba.txt"
    destino = os.path.join(SHARED_FOLDER, nombre)
    assert os.path.isfile(destino)

    # 4. Su contenido debe ser idéntico
    assert open(destino, "rb").read() == contenido

    # 5. list_shared_files() debe listar este fichero
    archivos = list_shared_files()
    assert nombre in archivos

def test_add_file_no_existe():
    """
    Si se invoca add_file con una ruta inexistente, no debe levantar excepción,
    y SHARED_FOLDER sigue vacío.
    """
    ruta_erronea = "/ruta/que/no/existe/archivo.xyz"
    # No debe levantar excepción
    add_file(ruta_erronea)

    # SHARED_FOLDER continúa vacío
    archivos = list_shared_files()
    assert archivos == []
