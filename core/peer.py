# core/peer.py

from core.discovery import register_with_bootstrap
from core.index import list_shared_files, add_file
from core.transfer import start_file_server, download_file, remote_file_exists
from utils.config import DEFAULT_PEER_IP
from utils.logger import info, error

class Peer:
    def __init__(self, ip: str = DEFAULT_PEER_IP, port: int = 9000):
        self.ip = ip
        self.port = port
        self.known_nodes = []
        # Iniciamos el servidor P2P que atiende búsquedas y descargas
        start_file_server(self.ip, self.port)
        info(f"Peer inicializado en {self.ip}:{self.port}")

    def connect_to_bootstrap(self):
        """
        Llama a core.discovery.register_with_bootstrap() para
        registrarse y recibir la lista de nodos activos.
        """
        self.known_nodes = register_with_bootstrap(self.ip, self.port)
        if self.known_nodes:
            info("Lista de nodos conocidos tras registro:")
            for ip, port in self.known_nodes:
                print(f"  • {ip}:{port}")
        else:
            error("No se recibieron nodos conocidos del bootstrap.")

    def list_known_nodes(self):
        """
        Imprime por pantalla la lista de peers que conocemos (tras registro).
        """
        if not self.known_nodes:
            print("No hay nodos conocidos. → Ejecuta 'Connectar al bootstrap' primero.")
            return
        print("Nodos conocidos:")
        for ip, port in self.known_nodes:
            print(f"  • {ip}:{port}")

    def share_file(self, path: str):
        """
        Agrega (copia) un archivo de 'path' a la carpeta shared_files.
        """
        add_file(path)

    def list_local_files(self) -> list:
        """
        Retorna la lista de archivos en shared_files/.
        """
        return list_shared_files()

    def search_file(self, filename: str) -> list:
        """
        Realiza una búsqueda distribuida: para cada peer en self.known_nodes,
        llama a remote_file_exists(ip, port, filename). Devuelve la lista
        de (ip, port) que respondieron FOUND.
        """
        if not self.known_nodes:
            error("No hay nodos conocidos. Conéctate primero al bootstrap.")
            return []

        info(f"Iniciando búsqueda de '{filename}' en {len(self.known_nodes)} nodos...")
        found_list = []
        for ip, port in self.known_nodes:
            if remote_file_exists(ip, port, filename):
                found_list.append((ip, port))

        return found_list

    def download_file(self, ip: str, port: int, filename: str):
        """
        Descarga el archivo especificado desde el peer (ip, port).
        """
        info(f"Iniciando descarga de '{filename}' desde {ip}:{port}...")
        download_file(ip, port, filename)
