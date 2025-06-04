# cli/main.py

import sys
from core.peer import Peer
from utils.logger import info, error

def main():
    print("=== DistriShare CLI (P2P Híbrido) ===")

    # Parámetros por línea de comandos permitidos:
    #  - python main.py <PUERTO>
    #  - python main.py <MI_IP> <PUERTO>
    if len(sys.argv) not in (2, 3):
        print("Uso:")
        print("  python main.py <PUERTO>             # escucha en 127.0.0.1:<PUERTO>")
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

    # Creamos el peer usando la IP y el puerto que toque
    peer = Peer(ip=mi_ip, port=puerto_propio)

    while True:
        print("\nMenú DistriShare:")
        print("1. Connectar al bootstrap node")
        print("2. Llistar tots els nodes coneguts")
        print("3. Llistar nodes del Bootstrap") 
        print("4. Llistar nodes del multicast")
        print("5. Buscar un fitxer")
        print("6. Descarregar un fitxer")
        print("7. Compartir fitxer")
        print("8. Veure fitxers locals")
        print("9. Activar descubrimiento multicast")
        print("0. Cerrar descubrimiento multicast")  
        print("99. Sortir")  

        choice = input("> ").strip()

        if choice == '1':
            peer.connect_to_bootstrap()

        elif choice == '2':
            peer.list_known_nodes()

        elif choice == '3':
            peer.list_bootstrap_nodes()

        elif choice == '4':
            peer.list_available_nodes()

        elif choice == '5':
            filename = input("Nom del fitxer a buscar: ").strip()
            if not filename:
                error("No has introduït cap nom de fitxer.")
                continue
            encontrados = peer.search_file(filename)
            if encontrados:
                print("✅ Fitxer trobat en els següents nodes:")
                for ip, port in encontrados:
                    print(f"   • {ip}:{port}")
            else:
                print("❌ Fitxer no trobat a cap node conegut.")

        elif choice == '6':
            ip = input("IP del node origen: ").strip()
            port_str = input("Port del node origen: ").strip()
            filename = input("Nom del fitxer a descarregar: ").strip()

            try:
                port = int(port_str)
            except ValueError:
                error("El port ha de ser un número enter.")
                continue

            if not ip or not filename:
                error("Tots els camps són obligatoris.")
                continue

            peer.download_file(ip, port, filename)

        elif choice == '7':
            path = input("Ruta completa del fitxer a compartir: ").strip()
            if not path:
                error("Has de proporcionar la ruta d'un fitxer.")
                continue
            peer.share_file(path)

        elif choice == '8':
            archivos = peer.list_local_files()
            if archivos:
                print("Fitxers disponibles localment (shared_files/):")
                for a in archivos:
                    print(f"   • {a}")
            else:
                print("No hi ha fitxers compartits locals.")
                
        elif choice == "9":
            peer.start_multicast()

        elif choice == "0":
            peer.stop_multicast()

        elif choice == "99":
            print("Sortint de DistriShare... Adeu!")
            sys.exit(0)

        else:
            error("Opció no vàlida. Torna-ho a provar.")

if __name__ == "__main__":
    main()
