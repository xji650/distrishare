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
from network.protocol import HELLO_PREFIX, GOODBYE_PREFIX
from utils.logger import info, debug, error

class MulticastDiscovery:
    """
    Gestiona el descubrimiento P2P por multicast:
      - Envía periódicamente mensajes HELLO
      - Escucha HELLO y GOODBYE de otros peers
      - Notifica al Peer que se suscribe cuando aparece o desaparece un peer
    """

    def __init__(self, my_ip: str, my_port: int,
                 callback_new_peer,
                 callback_peer_leave):
        """
        :param my_ip: IP local (por lo general '127.0.0.1' en pruebas locales)
        :param my_port: Puerto TCP en el que este peer atiende búsquedas/descargas
        :param callback_new_peer: función(peer_ip, peer_port) llamada al recibir HELLO
        :param callback_peer_leave: función(peer_ip, peer_port) llamada al recibir GOODBYE
        """
        self.my_ip = my_ip
        self.my_port = my_port
        self.callback_new_peer = callback_new_peer
        self.callback_peer_leave = callback_peer_leave

        # Conjunto para rastrear peers vistos (por HELLO) y no haber procesado antes
        self._peers_vistos = set()

        # Evento para detener threads
        self._stop_event = threading.Event()

        # Threads / sockets
        self.listen_thread = None
        self.sender_thread = None
        self.listen_sock = None
        self.send_sock = None

        self._start_listener()
        self._start_sender()

    def _start_listener(self):
        def listener():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except AttributeError:
                    pass
                sock.bind(('', MULTICAST_PORT))

                mreq = struct.pack("=4sl",
                                   socket.inet_aton(MULTICAST_GROUP),
                                   socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP,
                                socket.IP_ADD_MEMBERSHIP,
                                mreq)

                self.listen_sock = sock
                info(f"[Multicast] Listener unido a {MULTICAST_GROUP}:{MULTICAST_PORT}")

                while not self._stop_event.is_set():
                    try:
                        sock.settimeout(1.0)  # para poder chequear el stop_event
                        data, addr = sock.recvfrom(1024)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        error(f"[Multicast] Listener error: {e}")
                        break

                    if not data:
                        continue

                    mensaje = data.decode().strip()
                    debug(f"[Multicast] Recibido '{mensaje}' de {addr}")

                    # --- Caso HELLO ---
                    if mensaje.startswith(HELLO_PREFIX):
                        contenido = mensaje[len(HELLO_PREFIX):]  # "127.0.0.1:9001"
                        try:
                            ip_str, port_str = contenido.split(":")
                            puerto = int(port_str)
                        except Exception:
                            debug(f"[Multicast] HELLO malformado: {contenido}")
                            continue

                        # Ignorar nuestro propio HELLO
                        if ip_str == self.my_ip and puerto == self.my_port:
                            continue

                        peer_tuple = (ip_str, puerto)
                        # Si no lo habíamos visto antes, lo notificamos
                        if peer_tuple not in self._peers_vistos:
                            self._peers_vistos.add(peer_tuple)
                            info(f"[Multicast] Nuevo peer descubierto: {peer_tuple}")
                            self.callback_new_peer(ip_str, puerto)

                    # --- Caso GOODBYE ---
                    elif mensaje.startswith(GOODBYE_PREFIX):
                        contenido = mensaje[len(GOODBYE_PREFIX):]
                        try:
                            ip_str, port_str = contenido.split(":")
                            puerto = int(port_str)
                        except Exception:
                            debug(f"[Multicast] GOODBYE malformado: {contenido}")
                            continue

                        # Ignorar si es nuestro propio GOODBYE
                        if ip_str == self.my_ip and puerto == self.my_port:
                            continue

                        peer_tuple = (ip_str, puerto)
                        if peer_tuple in self._peers_vistos:
                            # Marcamos que el peer "abandonó"
                            self._peers_vistos.discard(peer_tuple)
                            info(f"[Multicast] Peer dejó la red: {peer_tuple}")
                            self.callback_peer_leave(ip_str, puerto)

                    # Si no es HELLO ni GOODBYE, lo ignoramos

                try:
                    sock.close()
                except Exception:
                    pass

            except Exception as e:
                error(f"[Multicast] Excepción en listener: {e}")

        self.listen_thread = threading.Thread(target=listener, daemon=True)
        self.listen_thread.start()

    def _start_sender(self):
        def sender():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                ttl_bytes = struct.pack('b', MULTICAST_TTL)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bytes)
                self.send_sock = sock
                info(f"[Multicast] Sender preparado para {MULTICAST_GROUP}:{MULTICAST_PORT}")

                while not self._stop_event.is_set():
                    mensaje = f"{HELLO_PREFIX}{self.my_ip}:{self.my_port}"
                    sock.sendto(mensaje.encode(),
                                (MULTICAST_GROUP, MULTICAST_PORT))
                    debug(f"[Multicast] Enviado '{mensaje}' al grupo")

                    # Esperar MULTICAST_INTERVAL segundos, 
                    # pero chequear periódicamente si hay que detenerse:
                    intervalo = int(MULTICAST_INTERVAL * 10)
                    for _ in range(intervalo):
                        if self._stop_event.is_set():
                            break
                        time.sleep(0.1)

                try:
                    sock.close()
                except Exception:
                    pass

            except Exception as e:
                error(f"[Multicast] Excepción en sender: {e}")

        self.sender_thread = threading.Thread(target=sender, daemon=True)
        self.sender_thread.start()

    def close(self):
        """
        Detiene el envío periódico de HELLO y envía un único GOODBYE
        para que los demás nodos sepan que hemos abandonado la red.
        """
        # 1) Enviar un mensaje GOODBYE antes de bajar el listener
        try:
            goodbye_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            ttl_bytes = struct.pack('b', MULTICAST_TTL)
            goodbye_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bytes)
            mensaje = f"{GOODBYE_PREFIX}{self.my_ip}:{self.my_port}"
            goodbye_sock.sendto(mensaje.encode(),
                                 (MULTICAST_GROUP, MULTICAST_PORT))
            goodbye_sock.close()
            debug(f"[Multicast] Enviado GOODBYE: '{mensaje}' al grupo")
        except Exception as e:
            error(f"[Multicast] No se pudo enviar GOODBYE: {e}")

        # 2) Señalar a los hilos que deben detenerse
        self._stop_event.set()

        # 3) Esperar que los threads terminen
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        if self.sender_thread:
            self.sender_thread.join(timeout=2)

        # 4) Cerrar cualquier socket abierto
        try:
            if self.listen_sock:
                self.listen_sock.close()
        except Exception:
            pass
        try:
            if self.send_sock:
                self.send_sock.close()
        except Exception:
            pass

        info("[Multicast] MulticastDiscovery cerrado.")
