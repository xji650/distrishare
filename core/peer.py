# core/peer.py

from core.discovery    import register_with_bootstrap
from core.index        import list_shared_files, add_file
from core.transfer     import start_file_server, download_file, remote_file_exists
from core.multicast    import MulticastDiscovery
from utils.config      import DEFAULT_PEER_IP
from utils.logger      import info, error

class Peer:
    def __init__(self, ip: str = DEFAULT_PEER_IP, port: int = 9000):
        """
        Inicializa el Peer:
        - Guarda IP y puerto propios.
        - known_nodes es un set para evitar duplicados.
        - Inicia servidor TCP para búsquedas/descargas.
        - Inicia discovery por multicast (envío/recepción HELLO).
        """
        self.ip = ip
        self.port = port
        self.known_nodes = set()

        # 1) Servidor TCP
        start_file_server(self.ip, self.port)
        info(f"Peer inicializado en {self.ip}:{self.port}")

        # 2) Discovery híbrido: multicast HELLO
        self.multicast = MulticastDiscovery(
            my_ip=self.ip,
            my_port=self.port,
            callback_new_peer=self._on_new_multicast_peer
        )

    def _on_new_multicast_peer(self, peer_ip: str, peer_port: int):
        """
        Callback de MulticastDiscovery cuando se recibe un HELLO de otro peer.
        """
        tup = (peer_ip, peer_port)
        if tup not in self.known_nodes:
            self.known_nodes.add(tup)
            info(f"[Peer] Añadido vía multicast → {tup}")

    def connect_to_bootstrap(self):
        """
        Registro en Bootstrap y obtención inicial de nodos.
        """
        nodos = register_with_bootstrap(self.ip, self.port)
        for (ip, puerto) in nodos:
            if (ip, puerto) != (self.ip, self.port):
                if (ip, puerto) not in self.known_nodes:
                    self.known_nodes.add((ip, puerto))
        info(f"[Peer] known_nodes tras registro bootstrap: {self.known_nodes}")

    def list_known_nodes(self):
        """
        Muestra los peers que conocemos (bootstrap + multicast).
        """
        if not self.known_nodes:
            print("No hay nodos conocidos aún.")
            return
        print("Nodos coneguts:")
        for ip, puerto in self.known_nodes:
            print(f"  • {ip}:{puerto}")

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

    def search_file(self, filename: str) -> list:
        """
        Búsqueda distribuida: intenta remote_file_exists en cada peer conocido.
        """
        if not self.known_nodes:
            error("No hay nodos conocidos. Conéctate primero al bootstrap o espera multicast.")
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
