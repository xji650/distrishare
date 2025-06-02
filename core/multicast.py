# core/multicast.py

import socket
import struct
import threading
import time

from utils.config import (
    MULTICAST_GROUP,
    MULTICAST_PORT,
    MULTICAST_TTL,
    MULTICAST_INTERVAL
)
from network.protocol import HELLO_PREFIX
from utils.logger import info, debug, error

class MulticastDiscovery:
    """
    Clase que se encarga de:
    - Unirse a un grupo UDP multicast para recibir mensajes HELLO de otros peers.
    - Enviar periódicamente un mensaje HELLO con nuestra IP y puerto.
    """

    def __init__(self, my_ip: str, my_port: int, callback_new_peer):
        """
        :param my_ip: IP local del peer (en general '127.0.0.1' si pruebas en local)
        :param my_port: Puerto TCP en el que este peer atiende búsquedas/descargas
        :param callback_new_peer: función que se llama cada vez que aparece un peer nuevo
        """
        self.my_ip = my_ip
        self.my_port = my_port
        self.callback_new_peer = callback_new_peer

        # Para no procesar nuestro propio HELLO repetidamente:
        self._last_hello_sent_time = 0

        # Creamos sockets multicast por separado:
        self.listen_sock = None
        self.send_sock = None

        # Conjunto para rastrear pares (ip,port) ya vistos vía multicast:
        self._peers_vistos = set()

        # Iniciar los hilos de listener y sender
        self._start_listener()
        self._start_sender()

    def _start_listener(self):
        """
        Lanza en un hilo el socket UDP que se une al grupo multicast y espera mensajes.
        """
        def listener():
            try:
                # Creamos socket UDP para escuchar en el grupo multicast
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # En sistemas Linux es suficiente con SO_REUSEADDR; en algunos entornos Windows
                # puede añadirse SO_REUSEPORT (no siempre disponible).
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except AttributeError:
                    pass  

                # Asignar (bind) a la interfaz ANY en el puerto MULTICAST_PORT
                sock.bind(('', MULTICAST_PORT))

                # Unirse al grupo multicast
                mreq = struct.pack("=4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

                info(f"[Multicast] Listener unido a {MULTICAST_GROUP}:{MULTICAST_PORT}")

                while True:
                    data, addr = sock.recvfrom(1024)
                    if not data:
                        continue
                    mensaje = data.decode().strip()
                    debug(f"[Multicast] Recibido '{mensaje}' de {addr}")

                    # Procesar solo mensajes que empiecen con HELLO_PREFIX
                    if mensaje.startswith(HELLO_PREFIX):
                        contenido = mensaje[len(HELLO_PREFIX):]  # "127.0.0.1:9001"
                        try:
                            ip_str, port_str = contenido.split(":")
                            puerto = int(port_str)
                        except Exception:
                            debug(f"[Multicast] Mensaje HELLO malformado: {contenido}")
                            continue

                        # Ignorar nuestro propio HELLO
                        if ip_str == self.my_ip and puerto == self.my_port:
                            continue

                        peer_tuple = (ip_str, puerto)
                        if peer_tuple not in self._peers_vistos:
                            self._peers_vistos.add(peer_tuple)
                            info(f"[Multicast] Nuevo peer descubierto: {peer_tuple}")
                            # Llamar al callback para que Peer lo añada a known_nodes
                            self.callback_new_peer(ip_str, puerto)
            except Exception as e:
                error(f"[Multicast] Excepción en listener: {e}")

        t = threading.Thread(target=listener, daemon=True)
        t.start()

    def _start_sender(self):
        """
        Lanza en un hilo un loop que cada MULTICAST_INTERVAL envía un HELLO al grupo.
        """
        def sender():
            try:
                # Creamos socket UDP para enviar a grupo multicast
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                # Establecer TTL (Time-To-Live) para multicast
                ttl_bytes = struct.pack('b', MULTICAST_TTL)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bytes)
                info(f"[Multicast] Sender preparado para {MULTICAST_GROUP}:{MULTICAST_PORT}")

                while True:
                    mensaje = f"{HELLO_PREFIX}{self.my_ip}:{self.my_port}"
                    # Enviar al grupo multicast
                    sock.sendto(mensaje.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
                    debug(f"[Multicast] Enviado '{mensaje}' al grupo")
                    time.sleep(MULTICAST_INTERVAL)
            except Exception as e:
                error(f"[Multicast] Excepción en sender: {e}")

        t = threading.Thread(target=sender, daemon=True)
        t.start()
