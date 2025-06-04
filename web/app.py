# web/app.py

import os
import sys
import argparse

# --------------------------------------------------
#  1. Añadimos la carpeta padre para que Python
#     encuentre los paquetes core/ y utils/
# --------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --------------------------------------------------
#  2. Importamos Flask y la lógica de Peer
# --------------------------------------------------
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

# Importamos la clase Peer, la función is_node_alive y la función register_with_bootstrap
from core.peer import Peer, is_node_alive
from core.discovery import register_with_bootstrap
from utils.config import SHARED_FOLDER, DOWNLOAD_FOLDER

# --------------------------------------------------
# 3. Procesamos argumentos de línea de comandos
# --------------------------------------------------
parser = argparse.ArgumentParser(
    description="Arranca DistriShare Web + Peer P2P"
)
parser.add_argument(
    "--peer-ip",
    type=str,
    default="127.0.0.1",
    help="IP en la que este peer P2P escuchará (por defecto 127.0.0.1)"
)
parser.add_argument(
    "--peer-port",
    type=int,
    default=8001,
    help="Puerto TCP en el que este peer P2P escuchará (por defecto 8001)"
)
parser.add_argument(
    "--flask-host",
    type=str,
    default="0.0.0.0",
    help="Host/IP en el que Flask arrancará (por defecto 0.0.0.0)"
)
parser.add_argument(
    "--flask-port",
    type=int,
    default=5000,
    help="Puerto HTTP en el que Flask arrancará (por defecto 5000)"
)
args = parser.parse_args()

PEER_IP = args.peer_ip
PEER_PORT = args.peer_port
FLASK_HOST = args.flask_host
FLASK_PORT = args.flask_port

# --------------------------------------------------
# 4. Inicializamos Flask y el objeto Peer
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = "distri_flask_secret_key_2025"

# Creamos el Peer usando la IP y el puerto que pasemos por argumentos
peer = Peer(ip=PEER_IP, port=PEER_PORT)

# Nos aseguramos de que existan las carpetas de shared_files y downloads
if not os.path.isdir(SHARED_FOLDER):
    os.makedirs(SHARED_FOLDER)
if not os.path.isdir(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --------------------------------------------------
# 5. Definición de rutas de Flask
# --------------------------------------------------

@app.route("/")
def index():
    """
    Página de inicio (Dashboard) con botones para las diferentes acciones.
    """
    return render_template("index.html")


@app.route("/conectar_bootstrap", methods=["POST"])
def conectar_bootstrap():
    """
    Llama a peer.connect_to_bootstrap() y muestra flash messages.
    Esto registra al peer en el servidor Bootstrap, pero no devuelve
    la lista completa. Sólo llena peer.known_nodes internamente.
    """
    try:
        peer.connect_to_bootstrap()
        flash("Conectado al Bootstrap Server correctamente.", "success")
    except Exception as e:
        flash(f"No se pudo conectar al Bootstrap: {e}", "danger")
    return redirect(url_for("index"))


@app.route("/listar_nodos")
def listar_nodos():
    """
    Lista los nodos conocidos en peer.known_nodes y comprueba su estado TCP
    usando la función global is_node_alive().
    """
    known = list(peer.known_nodes)  # [(ip, puerto), ...]
    estados = []
    for ip, puerto in known:
        vivo = is_node_alive(ip, puerto)
        estados.append({
            "ip": ip,
            "port": puerto,
            "vivo": vivo
        })
    return render_template("listar_nodos.html", estados=estados, title="Nodos Conocidos")


@app.route("/listar_multicast")
def listar_multicast():
    """
    Lista los nodos descubiertos por multicast en peer.available_nodes.
    """
    available = list(peer.available_nodes)  # [(ip, puerto), ...]
    estados = []
    for ip, puerto in available:
        vivo = is_node_alive(ip, puerto)
        estados.append({
            "ip": ip,
            "port": puerto,
            "vivo": vivo
        })
    return render_template("listar_nodos.html", estados=estados, title="Nodos Disponibles")


@app.route("/listar_bootstrap")
def listar_bootstrap():
    """
    Recupera la lista de nodos registrados en el Bootstrap Server usando
    la función global register_with_bootstrap, y luego muestra su estado TCP.
    Además, añade esos nodos a peer.known_nodes para futuras búsquedas.
    """
    try:
        # register_with_bootstrap retorna lista de tuplas [(ip, puerto), ...]
        nodos = register_with_bootstrap(peer.ip, peer.port)

        # Añadimos cada nodo (excluyendo este mismo) a peer.known_nodes
        for (ip, puerto) in nodos:
            tup = (ip, puerto)
            if tup != (peer.ip, peer.port) and tup not in peer.known_nodes:
                peer.known_nodes.add(tup)

        estados = []
        for ip, puerto in nodos:
            vivo = is_node_alive(ip, puerto)
            estados.append({
                "ip": ip,
                "port": puerto,
                "vivo": vivo
            })
        return render_template("listar_nodos.html", estados=estados, title="Nodos en Bootstrap")
    except Exception as e:
        flash(f"No se pudo obtener nodos del Bootstrap: {e}", "danger")
        return redirect(url_for("index"))


@app.route("/buscar", methods=["GET", "POST"])
def buscar_archivo():
    """
    Muestra el formulario para buscar archivos (GET). Si llega un POST,
    toma el nombre, llama a peer.search_file() y muestra resultados.
    """
    if request.method == "POST":
        filename = request.form.get("filename", "").strip()
        if not filename:
            flash("Debes indicar un nombre de archivo para buscar.", "warning")
            return redirect(url_for("buscar_archivo"))
        encontrados = peer.search_file(filename)
        return render_template("resultados_busqueda.html", filename=filename, encontrados=encontrados)
    return render_template("buscar.html")


@app.route("/descargar", methods=["POST"])
def descargar_archivo():
    """
    Recibe ip, puerto y nombre de archivo por formulario,
    y lanza peer.download_file(...).
    """
    ip = request.form.get("ip", "").strip()
    port_str = request.form.get("port", "").strip()
    filename = request.form.get("filename", "").strip()

    # Validamos puerto
    try:
        port = int(port_str)
    except ValueError:
        flash("El puerto debe ser un número entero.", "danger")
        return redirect(url_for("buscar_archivo"))

    if not ip or not filename:
        flash("IP, puerto y nombre de archivo son obligatorios.", "warning")
        return redirect(url_for("buscar_archivo"))

    try:
        peer.download_file(ip, port, filename)
        flash(f"Descarga de '{filename}' iniciada. Revisa la carpeta {DOWNLOAD_FOLDER}.", "success")
    except Exception as e:
        flash(f"No se pudo descargar: {e}", "danger")
    return redirect(url_for("index"))


@app.route("/compartir", methods=["GET", "POST"])
def compartir():
    """
    Muestra el formulario para compartir un archivo local (GET).
    Si es POST, toma la ruta, llama a peer.share_file(path).
    """
    if request.method == "POST":
        path = request.form.get("path", "").strip()
        if not path:
            flash("Debes indicar la ruta completa del archivo a compartir.", "warning")
            return redirect(url_for("compartir"))
        try:
            peer.share_file(path)
            flash(f"Archivo '{os.path.basename(path)}' compartido correctamente.", "success")
        except Exception as e:
            flash(f"No se pudo compartir: {e}", "danger")
        return redirect(url_for("index"))
    return render_template("compartir.html")


@app.route("/locales")
def archivos_locales():
    """
    Muestra la lista de archivos que este peer tiene en shared_files/.
    """
    archivos = peer.list_local_files()
    return render_template("listar_locales.html", archivos=archivos)

@app.route("/descargas")
def archivos_descargados():
    """
    Muestra la lista de archivos que este peer ha descargado (downloads/).
    """
    archivos = peer.list_downloaded_files()
    return render_template("listar_descargas.html", archivos=archivos)

@app.route("/descargas/<filename>")
def servir_descarga(filename):
    """
    Permite al navegador descargar un archivo de la carpeta DOWNLOAD_FOLDER.
    """
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


# ─────────────────────────────────────────────────────
# RUTAS NUEVAS PARA MULTICAST Y SHUTDOWN
# ─────────────────────────────────────────────────────

@app.route("/start_multicast", methods=["POST"])
def start_multicast():
    """
    Activa el descubrimiento multicast en el peer.
    """
    try:
        peer.start_multicast()
        flash("Descubrimiento multicast ACTIVADO.", "success")
    except Exception as e:
        flash(f"No se pudo activar multicast: {e}", "danger")
    return redirect(url_for("index"))


@app.route("/stop_multicast", methods=["POST"])
def stop_multicast():
    """
    Detiene el descubrimiento multicast en el peer.
    """
    try:
        peer.stop_multicast()
        flash("Descubrimiento multicast CERRADO.", "warning")
    except Exception as e:
        flash(f"No se pudo cerrar multicast: {e}", "danger")
    return redirect(url_for("index"))


@app.route("/shutdown", methods=["POST"])
def shutdown():
    """
    Intenta apagar la aplicación Flask (sólo en modo desarrollo).
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        flash("No se pudo detener el servidor (no estás en modo desarrollo).", "danger")
        return redirect(url_for("index"))
    func()
    return "Servidor Flask detenido."

# --------------------------------------------------
# 6. Run: arrancamos Flask en el host y puerto indicados
# --------------------------------------------------
if __name__ == "__main__":
    # Flask escucha en FLASK_HOST:FLASK_PORT y Peer en PEER_IP:PEER_PORT
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
