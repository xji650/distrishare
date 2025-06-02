# Definicions de missatges/comunicació
# network/protocol.py

# Prefijo para búsqueda de fichero:
SEARCH_PREFIX = "SEARCH:"
FOUND         = "FOUND"
NOT_FOUND     = "NOT_FOUND"

# Prefijo para multicast HELLO:
HELLO_PREFIX = "HELLO:"   # Formato (texto) → "HELLO:127.0.0.1:9001"

# Respuestas posibles:
FOUND = "FOUND"
NOT_FOUND = "NOT_FOUND"

# Si se recibe un mensaje que no empiece con SEARCH_, se interpreta como
# petición de descarga: el contenido del mensaje = nombre de fichero.
