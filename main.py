from core.node import Node

def main():
    node = Node()

    while True:
        print("\nBenvingut a DistriShare!")
        print("1. Connectar al bootstrap node")
        print("2. Llistar nodes coneguts")
        print("6. Sortir")

        option = input("> ")

        if option == '1':
            node.connect_to_bootstrap()
        elif option == '2':
            node.list_known_nodes()
        elif option == '5':
            path = input("Ruta del fitxer a compartir: ")
            node.share_file(path)
        elif option == '6':
            break
        else:
            print("Opció no vàlida.")

if __name__ == "__main__":
    main()
