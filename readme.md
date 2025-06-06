# DistriShare

**DistriShare** és una aplicació distribuïda de compartició de fitxers entre usuaris basada en una arquitectura **P2P híbrida**. Combina un **servidor bootstrap** centralitzat per facilitar la connexió inicial i un sistema de **descobriment distribuït** (UDP multicast) per mantenir una xarxa descentralitzada i resilient.

---
## Presentació PPT dia 05/06/2025 a classe: [DistriShare.ppt]()

---

## 1. Característiques Principals

- Xarxa **peer-to-peer** amb servidor central de fitxers  
- **Descobriment de nodes** via Bootstrap Server i UDP Multicast  
- **Compartició de fitxers** entre usuaris directament (TCP)  
- **Indexació distribuïda**: cada peer manté un índex propi  
- CLI per navegar, buscar i descarregar arxius  

---

## 2. Estructura del Projecte

- `cli/`: contiene `main.py`, la interfaz de línea de comandos.
- `core/`: lógica de peer (descubrimiento, índice, transferencia).
- `network/`: bootstrap server y protocolo de mensajes.
- `utils/`: configuración y logger.
- `shared_files/`: carpeta donde cada peer almacena los archivos que desea compartir.
- `downloads/`: carpeta donde cada peer almacena los archivos descargados de otros peers.

```
DistriShare/
├── core/
│   ├── peer.py            # Lógica principal del Peer (registro, búsqueda, descarga)
│   ├── multicast.py       # Descubrimiento de nodos via UDP multicast
│   ├── transfer.py        # Transferencia de archivos entre peers
│   └── index.py           # Gestión de archivos locales (shared_files/ y downloads/)
├── network/
│   ├── bootstrap_server.py # Servidor central de registro
│   ├── protocol.py        # Definición de mensajes (HELLO, SEARCH, etc.)
│   └── discovery.py       # Conexión al Bootstrap
├── cli/
│   └── main.py            # Interfaz de línea de comandos
├── web/
│   ├── app.py             # Servidor Flask para interfaz web
│   └── templates/         # Plantillas HTML
└── utils/
    ├── config.py          # Configuración (IPs, puertos, carpetas)
    └── logger.py          # Sistema de logging

```

---

## 3. Com executar (LAN local)

### 3.1. CLI
#### 1. Inicia el Bootstrap Server (se queda escuchando en el puerto 8000):
```bash
python3 -m network.bootstrap_server
```

#### 2. Inicia un Peer (por ejemplo en otro terminal), asignándole un puerto:
```bash
python3 -m cli.main 9000
```

#### 3. Inicia otro Peer (por ejemplo en otro terminal), asignándole un ip y un puerto:
```bash
python3 -m cli.main 192.168.1.42 9100
```

##### Reemplaza 9000 por el puerto libre que quieras para ese peer (p.ej. 9001, 9002, …).

#### 4. Funcionalitats del CLI

```
Conexión
   1.1 Conectar al nodo Bootstrap
   1.2 Activar descubrimiento multicast
   1.3 Detener descubrimiento multicast

Nodos
   2.1 Listar todos los nodos conocidos
   2.2 Listar nodos del Bootstrap
   2.3 Listar nodos detectados por multicast

Gestión de archivos
   3.1 Compartir un archivo (en shared_files/)
   3.2 Ver archivos compartidos localmente (shared_files/)
   3.3 Buscar un archivo en la red
   3.4 Descargar un archivo de otro peer
   3.5 Ver archivos descargados (downloads/)

0. Salir
```
---
### 3.2. WEB
#### 1. Inicia el Bootstrap Server (se queda escuchando en el puerto 8000):
```bash
python3 -m network.bootstrap_server
```

#### 2. Inicia un Peer (por ejemplo en otro terminal), asignándole un puerto:
```bash
python -m web.app --peer-port 9000 --flask-port 5000
```

#### 3. Inicia otro Peer (por ejemplo en otro terminal), asignándole un ip y un puerto:
```bash
python -m web.app --peer-ip 90.167.87.98 --peer-port 9002 --flask-port 5002
```

##### Reemplaza 9000 por el puerto libre que quieras para ese peer (p.ej. 9001, 9002, …).
---
### 4. Para caso WAN (Internet)

#### Requisitos: Forwarding de puertos en el router para TCP (ej: 9000-9010).
#### IP pública estática o DDNS para peers servidores.
#### Inicia Peer asignándole un ip y un puerto (CLI):
```bash
python3 -m cli.main 192.168.1.42 9100
```
#### Inicia Peer asignándole un ip y un puerto (WEB):
```bash
python -m web.app --peer-ip 90.167.87.98 --peer-port 9002 --flask-port 5002
```
---

## 5. Arquitectura del Sistema

### Componentes Principales

| Componente             | Función                                                                 |
|------------------------|--------------------------------------------------------------------------|
| **Bootstrap Server**   | Registra peers y devuelve la lista de nodos activos.                     |
| **Peer (Nodo P2P)**    | Gestiona conexiones, comparte archivos y responde a búsquedas.           |
| **Multicast Discovery**| Anuncia peers en la red local mediante UDP multicast (HELLO/GREETING).   |
| **Transfer Manager**   | Maneja descargas y subidas de archivos vía TCP (SEARCH/DOWNLOAD).        |

---
## 6. Herramientas Usados

### Python 3
### Entorno virtual python (venv)
### WSL para simular Linux en Windows 
### VSC
### Control de versiones con Git - GitHub
### Web: Flask + Jinja2 (Templates)

---
## 7. Conceptes Aplicats de Computació Distribuïda

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


