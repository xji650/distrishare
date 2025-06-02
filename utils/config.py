# utils/config.py
import os

# Dirección del Bootstrap Server
BOOTSTRAP_IP = '127.0.0.1'
BOOTSTRAP_PORT = 8000

# Carpetas locales
SHARED_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'shared_files')
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'downloads')

# Parámetros por defecto de un peer
DEFAULT_PEER_IP = '127.0.0.1'
# El puerto se lo asignaremos desde CLI
