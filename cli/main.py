# cli/main.py

import sys
from core.peer import Peer
from utils.logger import info, error

def main():
    print("=== DistriShare CLI (P2P Híbrido) ===")

    # Validación de argumentos por línea de comandos:
    #   python main.py <PUERTO>
    #   python main.py <MI_IP> <PUERTO>
    if len(sys.argv) not in (2, 3):
        print("Uso:")
        print("  python main.py <PUERTO>            # escucha en 127.0.0.1:<PUERTO>")
        print("  python main.py <MI_IP> <PUERTO>    # escucha en <MI_IP>:<PUERTO>")
        sys.exit(1)

    if len(sys.argv) == 2:
        # Solo puerto → IP por defecto = localhost
        mi_ip = '127.0.0.1'
        try:
            puerto_propio = int(sys.argv[1])
        except ValueError:
            print("Error: el puerto debe ser un entero.")
            sys.exit(1)
    else:
        # IP + puerto
        mi_ip = sys.argv[1]
        try:
            puerto_propio = int(sys.argv[2])
        except ValueError:
            print("Error: el puerto debe ser un entero.")
            sys.exit(1)

    # Creamos el peer usando la IP y el puerto indicados
    peer = Peer(ip=mi_ip, port=puerto_propio)

    while True:
        print("\n----------- MENÚ PRINCIPAL -----------")
        print("Conexión")
        print("   1.1 Conectar al nodo Bootstrap")
        print("   1.2 Activar descubrimiento multicast")
        print("   1.3 Detener descubrimiento multicast")
        print("")
        print("Nodos")
        print("   2.1 Listar todos los nodos conocidos")
        print("   2.2 Listar nodos del Bootstrap")
        print("   2.3 Listar nodos detectados por multicast")
        print("")
        print("Gestión de archivos")
        print("   3.1 Compartir un archivo (en shared_files/)")
        print("   3.2 Ver archivos compartidos localmente (shared_files/)")
        print("   3.3 Buscar un archivo en la red")
        print("   3.4 Descargar un archivo de otro peer")
        print("   3.5 Ver archivos descargados (downloads/)")
        print("")
        print("0. Salir")
        print("---------------------------------------")

        choice = input("> ").strip()

        # 1. Conexión
        if choice == '1.1' or choice.lower() == '1.1':
            peer.connect_to_bootstrap()

        elif choice == '1.2' or choice.lower() == '1.2':
            peer.start_multicast()

        elif choice == '1.3' or choice.lower() == '1.3':
            peer.stop_multicast()

        # 2. Nodos
        elif choice == '2.1' or choice.lower() == '2.1':
            peer.list_known_nodes()

        elif choice == '2.2' or choice.lower() == '2.2':
            peer.list_bootstrap_nodes()

        elif choice == '2.3' or choice.lower() == '2.3':
            peer.list_available_nodes()

        # 3. Gestión de archivos
        elif choice == '3.1' or choice.lower() == '3.1':
            path = input("Ruta completa del archivo a compartir: ").strip()
            if not path:
                error("Debes indicar la ruta de un archivo.")
                continue
            peer.share_file(path)

        elif choice == '3.2' or choice.lower() == '3.2':
            archivos = peer.list_local_files()
            if archivos:
                print("Archivos compartidos localmente (shared_files/):")
                for a in archivos:
                    print(f"   • {a}")
            else:
                print("No hay archivos compartidos en shared_files/.")

        elif choice == '3.3' or choice.lower() == '3.3':
            filename = input("Nombre del archivo a buscar: ").strip()
            if not filename:
                error("No has introducido ningún nombre de archivo.")
                continue
            encontrados = peer.search_file(filename)
            if encontrados:
                print("✅ Archivo encontrado en los siguientes peers:")
                for ip, port in encontrados:
                    print(f"   • {ip}:{port}")
            else:
                print("❌ No se encontró el archivo en ningún peer conocido.")

        elif choice == '3.4' or choice.lower() == '3.4':
            ip = input("IP del peer origen: ").strip()
            port_str = input("Puerto del peer origen: ").strip()
            filename = input("Nombre del archivo a descargar: ").strip()

            try:
                port = int(port_str)
            except ValueError:
                error("El puerto debe ser un número entero.")
                continue

            if not ip or not filename:
                error("Todos los campos son obligatorios.")
                continue

            peer.download_file(ip, port, filename)

        elif choice == '3.5' or choice.lower() == '3.5':
            archivos_desc = peer.list_downloaded_files()
            if archivos_desc:
                print("Archivos descargados (downloads/):")
                for a in archivos_desc:
                    print(f"   • {a}")
            else:
                print("No hay archivos descargados todavía.")

        # 0. Salir
        elif choice == '0' or choice.lower() == '0':
            print("Saliendo de DistriShare... ¡Hasta luego!")
            sys.exit(0)

        else:
            error("Opción no válida. Por favor, introduce el número correspondiente.")


if __name__ == "__main__":
    main()
