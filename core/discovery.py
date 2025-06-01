import socket
import json

def register_with_bootstrap(my_ip, my_port, bootstrap_ip='127.0.0.1', bootstrap_port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((bootstrap_ip, bootstrap_port))
        request = {'type': 'register', 'ip': my_ip, 'port': my_port}
        s.sendall(json.dumps(request).encode())
        data = s.recv(1024)
        return json.loads(data.decode())['nodes']
