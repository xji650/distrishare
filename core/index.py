import os

SHARED_FOLDER = 'shared_files'

def list_shared_files():
    return os.listdir(SHARED_FOLDER)

def add_file(path):
    if os.path.exists(path):
        filename = os.path.basename(path)
        dest = os.path.join(SHARED_FOLDER, filename)
        with open(path, 'rb') as src, open(dest, 'wb') as dst:
            dst.write(src.read())
        print(f"Fitxer {filename} afegit per compartir.")
    else:
        print("Fitxer no trobat.")
