# core/peer.py

from core.discovery    import register_with_bootstrap
from core.index        import list_shared_files, add_file, list_downloaded_files
from core.transfer     import start_file_server, download_file, remote_file_exists
from core.multicast    import MulticastDiscovery
from utils.config      import DEFAULT_PEER_IP
from utils.logger      import info, error

import socket

def is_node_alive(ip: str, port: int) -> bool:
    """
    Comprueba si el peer (ip:port) responde al conectar TCP (ping rápido).
    """
    try:
        with socket.create_connection((ip, port), timeout=1):
            return True
    except:
        return False


class Peer:
    def __init__(self, ip: str = DEFAULT_PEER_IP, port: int = 9000):
        """
        Inicializa el Peer:
        - Guarda IP y puerto propios.
        - known_nodes = todos los que conocemos (bootstrap + multicast),
          available_nodes = subset que está en red (envió HELLO y no ha enviado GOODBYE).
        - Inicia servidor TCP para búsquedas/descargas.
        - Multicast desactivado hasta que se llame a start_multicast().
        """
        self.ip = ip
        self.port = port

        self.known_nodes = set()        # {(ip, port), ...}
        self.available_nodes = set()    # {(ip, port), ...}

        # 1) Servidor TCP (para búsquedas y descargas)
        start_file_server(self.ip, self.port)
        info(f"Peer inicializado en {self.ip}:{self.port}")

        # 2) Discovery híbrido: multicast (se crea cuando llamamos a start_multicast)
        self.multicast = None

    def _on_new_multicast_peer(self, peer_ip: str, peer_port: int):
        """
        Callback de MulticastDiscovery cuando llega un HELLO nuevo:
        Añadimos ese peer a known_nodes y available_nodes (si no existía).
        """
        tup = (peer_ip, peer_port)
        if tup not in self.known_nodes:
            self.known_nodes.add(tup)
        if tup not in self.available_nodes:
            self.available_nodes.add(tup)
        info(f"[Peer] Añadido vía multicast (activo) → {tup}")

    def _on_peer_leave(self, peer_ip: str, peer_port: int):
        """
        Callback de MulticastDiscovery cuando llega un GOODBYE de un peer:
        Eliminamos ese peer de available_nodes (pero lo dejamos en known_nodes).
        """
        tup = (peer_ip, peer_port)
        if tup in self.available_nodes:
            self.available_nodes.remove(tup)
            info(f"[Peer] Marcado como no disponible (GOODBYE) → {tup}")

    def start_multicast(self, force=False):
        """
        Activa multicast (si no estaba activo), creando la instancia de MulticastDiscovery.
        """
        if self.multicast is None or force:
            self.multicast = MulticastDiscovery(
                my_ip=self.ip,
                my_port=self.port,
                callback_new_peer=self._on_new_multicast_peer,
                callback_peer_leave=self._on_peer_leave
            )
            # Al activar multicast, también "nos damos de alta" como disponibles
            tup = (self.ip, self.port)
            if tup not in self.known_nodes:
                self.known_nodes.add(tup)
            if tup not in self.available_nodes:
                self.available_nodes.add(tup)

            info("[Peer] Multicast activado manualmente.")
        else:
            info("[Peer] Multicast ya estaba activo.")

    def stop_multicast(self):
        """
        Cierra el multicast (envía GOODBYE y detiene hilos).
        """
        if self.multicast:
            # Enviar GOODBYE y detener hilos
            self.multicast.close()
            self.multicast = None

            # Marcamos este peer como no disponible (pero lo mantenemos en known_nodes)
            tup = (self.ip, self.port)
            if tup in self.available_nodes:
                self.available_nodes.remove(tup)

            info("[Peer] Multicast cerrado.")
        else:
            info("[Peer] Multicast no estaba activo.")

    def connect_to_bootstrap(self):
        """
        Registro en el servidor bootstrap: retorna lista de nodos registrados.
        """
        nodos = register_with_bootstrap(self.ip, self.port)
        for (ip, puerto) in nodos:
            tup = (ip, puerto)
            if tup != (self.ip, self.port):
                if tup not in self.known_nodes:
                    self.known_nodes.add(tup)
                    # No asumimos que ese nodo esté “disponible” hasta que envíe HELLO
                    # (podría estar activo TCP, pero no participa en multicast).
        info(f"[Peer] known_nodes tras registro bootstrap: {self.known_nodes}")

    def list_known_nodes(self):
        """
        Opción 2. Imprime TODOS los peers que conocemos (bootstrap o multicast),
        marcando su estado TCP actual (vivo/caído).
        """
        if not self.known_nodes:
            print("No hay nodos conocidos. → Ejecuta 'Connectar al bootstrap' o espera multicast.")
            return

        print("Nodos coneguts (tots):")
        for ip, port in sorted(self.known_nodes):
            estado_tcp = "✅ vivo" if is_node_alive(ip, port) else "❌ caído"
            print(f"  • {ip}:{port}  →  {estado_tcp}")

    def list_available_nodes(self):
        """
        Opción 3. Imprime SOLO los peers que, por multicast, están activos (HELLO recibido sin GOODBYE)
        y además responden por TCP (listos para recibir datos).
        """
        if not self.known_nodes:
            print("No hi ha nodes disponibles. → Executa 'Connectar al bootstrap' o espera multicast.")
            return

        print("Nodos disponibles (vivos i sense GOODBYE):")
        activos = 0
        for ip, port in sorted(self.available_nodes):
            # Además comprobamos TCP para asegurarnos que realmente puede recibir datos
            if is_node_alive(ip, port):
                print(f"  • {ip}:{port}")
                activos += 1

        if activos == 0:
            print("⚠️  No hi ha nodes disponibles actualment.")

    def list_bootstrap_nodes(self):
        """
        Opción 4. Consulta al Bootstrap Server y muestra TODOS los nodos registrados allí.
        """
        # register_with_bootstrap devuelve la lista actual (y nos registra a nosotros si no está)
        try:
            nodos = register_with_bootstrap(self.ip, self.port)
        except Exception as e:
            error(f"[Peer] Error al obtener lista del Bootstrap: {e}")
            print("No se pudo conectar al Bootstrap Server.")
            return

        if not nodos:
            print("El Bootstrap no tiene ningún nodo registrado.")
            return

        print("Nodos actualmente registrados en el Bootstrap:")
        for ip, port in nodos:
            estado_tcp = "✅ vivo" if is_node_alive(ip, port) else "❌ caído"
            print(f"  • {ip}:{port}  →  {estado_tcp}")


    def share_file(self, path: str):
        """
        Copia el archivo de 'path' a shared_files/.
        """
        add_file(path)

    def list_local_files(self) -> list:
        """
        Retorna los archivos en shared_files/.
        """
        return list_shared_files()
    
    def list_downloaded_files(self) -> list:
        """
        Retorna los archivos que este peer ya ha descargado (downloads/).
        """
        return list_downloaded_files()

    def search_file(self, filename: str) -> list:
        """
        Búsqueda distribuida: intenta remote_file_exists en cada peer conocido.
        """
        if not self.known_nodes:
            error("No hi ha nodes coneguts. Connecta’t al bootstrap o espera multicast.")
            return []

        info(f"[Peer] Buscando '{filename}' entre {len(self.known_nodes)} nodos...")
        encontrados = []
        for (ip, puerto) in self.known_nodes:
            if remote_file_exists(ip, puerto, filename):
                encontrados.append((ip, puerto))
        return encontrados

    def download_file(self, ip: str, port: int, filename: str):
        """
        Descarga un archivo de (ip, port).
        """
        info(f"[Peer] Iniciando descarga de '{filename}' desde {ip}:{port}...")
        download_file(ip, port, filename)
