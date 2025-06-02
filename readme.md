# DistriShare

**DistriShare** és una aplicació distribuïda de compartició de fitxers entre usuaris basada en una arquitectura **P2P híbrida**. Combina un **servidor bootstrap** centralitzat per facilitar la connexió inicial i un sistema de **descobriment distribuït** (UDP multicast) per mantenir una xarxa descentralitzada i resilient.

---

## Característiques Principals

- Xarxa **peer-to-peer** sense servidor central de fitxers  
- **Descobriment de nodes** via Bootstrap Server i UDP Multicast  
- **Compartició de fitxers** entre usuaris directament (TCP)  
- **Indexació distribuïda**: cada peer manté un índex propi  
- CLI per navegar, buscar i descarregar arxius  

---

## Estructura del Projecte

- `cli/`: contiene `main.py`, la interfaz de línea de comandos.
- `core/`: lógica de peer (descubrimiento, índice, transferencia).
- `network/`: bootstrap server y protocolo de mensajes.
- `utils/`: configuración y logger.
- `shared_files/`: carpeta donde cada peer almacena los archivos que desea compartir.
- `downloads/`: carpeta donde cada peer almacena los archivos descargados de otros peers.

```
DistriShare/
│
├── cli/                     # Interfície per consola
│   └── main.py              # Menú principal del peer
│
├── core/                    # Lógica del peer
│   ├── peer.py              # Clase principal del peer
│   └── file_manager.py      # Gestor de fitxers locals
│
├── network/                 # Comunicacions en xarxa
│   ├── bootstrap_server.py  # Servidor centralitzat 
│   ├── discovery.py         # Discovery UDP (multicast)
│   ├── transfer.py          # Enviament/descàrrega de fitxers
│   └── protocol.py          # Definicions missatge/comunic
│
├── data/                    # Fitxers compartits i info
│   ├── shared/              # Carpeta amb fitxers compartits
│   └── known_peers.json     # Llista de peers coneguts
│
├── utils/
│   └── logger.py            # Logs i utilitats diverses
│
└── requirements.txt         # Dependències

```

---

## Com executar

### 1. Inicia el Bootstrap Server (se queda escuchando en el puerto 8000):
```bash
python3 -m network.bootstrap_server
```

### 2. Inicia un Peer (por ejemplo en otro terminal), asignándole un puerto:
```bash
python3 -m cli.main 9000
```
#### Reemplaza 9000 por el puerto libre que quieras para ese peer (p.ej. 9001, 9002, …).

### 3. Funcionalitats del CLI

```
1. Connectar al bootstrap per registrase
2. Llistar nodes coneguts
3. Buscar arxius a la xarxa
4. Descarregar arxiu indicant IP i port
5. Compartir arxiu locals mitjançant rutes del arxiu
6. Llistar arxius locals
7. Sortir
```

---

## Conceptes Aplicats de Computació Distribuïda

- Arquitectura **P2P híbrida**  
- **Discovery** de nodes (multicast + bootstrap)  
- **Transferència de fitxers** amb sockets TCP  
- Gestió de **fallades parcials** (el sistema continua si cau un peer)  
- **Indexació distribuïda** sense punt central  

---

## Autors

- *XiaoLong Ji*  
- *Assignatura: Computació Distribuïda i Aplicacions*  
- *Universitat de Lleida/ 3r curs GEI Igualada*  

---

## Contacte

Pots clonar, millorar i experimentar amb el projecte.  
Per dubtes, propostes o col·laboracions: *xj3@udl.cat*
