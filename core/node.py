from core.discovery import register_with_bootstrap
from core.transfer import start_file_server, download_file
from core import index


class Node:
    def __init__(self):
        self.ip = '127.0.0.1'
        self.port = 9000  # canvia si obres més d’un node
        self.known_nodes = []
        start_file_server(self.ip, self.port)

    def connect_to_bootstrap(self):
        self.known_nodes = register_with_bootstrap(self.ip, self.port)
        print("Nodes coneguts:")
        for node in self.known_nodes:
            print(f"- {node[0]}:{node[1]}")

    def list_known_nodes(self):
        if not self.known_nodes:
            print("Cap node conegut.")
        for node in self.known_nodes:
            print(f"- {node[0]}:{node[1]}")

    def share_file(self, path):
        index.add_file(path)

    def download_file(self, ip, port, filename):
        download_file(ip, port, filename)