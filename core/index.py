# core/index.py

import os
import shutil
from utils.config import SHARED_FOLDER
from utils.logger import info, error

def ensure_shared_folder():
    """
    Crea la carpeta shared_files si no existe.
    """
    if not os.path.isdir(SHARED_FOLDER):
        os.makedirs(SHARED_FOLDER)

def list_shared_files() -> list:
    """
    Retorna la lista de nombres de fichero dentro de shared_files/.
    """
    ensure_shared_folder()
    try:
        archivos = os.listdir(SHARED_FOLDER)
        return archivos
    except Exception as e:
        error(f"No se pudieron listar archivos compartidos: {e}")
        return []

def add_file(path: str):
    """
    Copia el archivo de 'path' a la carpeta shared_files/.
    """
    ensure_shared_folder()
    if not os.path.isfile(path):
        error(f"El archivo '{path}' no existe.")
        return

    filename = os.path.basename(path)
    destino = os.path.join(SHARED_FOLDER, filename)
    try:
        shutil.copy2(path, destino)
        info(f"Archivo '{filename}' agregado a shared_files.")
    except Exception as e:
        error(f"No se pudo copiar '{path}' → '{destino}': {e}")
