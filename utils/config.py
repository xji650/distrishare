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

# Multicast UDP para P2P híbrido 
MULTICAST_GROUP = '224.1.1.1'    # dirección de grupo multicast (IPv4 clase D)
MULTICAST_PORT  = 10000          # puerto UDP para multicast
MULTICAST_TTL   = 1              # Time-To-Live (cuántos saltos) para los mensajes
MULTICAST_INTERVAL = 5           # segundos entre cada anuncio "HELLO"

# El puerto se lo asignaremos desde CLI
