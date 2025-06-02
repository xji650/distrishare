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


# Recordatorio: cómo ejecutar y probar paso a paso

## 1. Arrancar el Bootstrap Server (terminal A)
```bash
cd distrishare
python3 -m network.bootstrap_server
```
Vemos algo como:
```css
[INFO 2025-06-02 12:00:00] [BOOTSTRAP] Servidor escuchando en 0.0.0.0:8000
```

## 2. Arrancar Peer 1 (terminal B)
```bash
cd distrishare
python3 -m cli.main 9001
```
Aparecerá:
```csharp
[INFO …] Peer inicializado en 127.0.0.1:9001
Menú DistriShare: …
```
En Peer 1 (Terminal B):
1. **Opc. 5** → Compartir fichero (por ejemplo: `/home/usuario/documentos/ejemplo.txt`).
2. **Opc. 1** → Connectar al bootstrap

Ahora `known_nodes = {('127.0.0.1', 9001)}` (él mismo).

3. **Opc. 2** → Llistar nodos conocidos

Aparecerá:
```text
• 127.0.0.1:9001
```

## 3. Arrancar Peer 2 (terminal C)
```bash
cd distrishare
python3 -m cli.main 9002
```
Aparece:
```csharp
[INFO …] Peer inicializado en 127.0.0.1:9002
```
En Peer 2 (Terminal C):
Sin hacer nada, después de unos segundos (~5 seg), debería recibir automáticamente el HELLO de Peer 1 por multicast y verlo en consola:
```less
[INFO …] [Multicast] Nuevo peer descubierto: ('127.0.0.1', 9001)
[INFO …] [Peer] Añadido vía multicast → ('127.0.0.1', 9001)
```

1. **Opc. 2** → Llistar nodos conocidos

Verás:
```text
• 127.0.0.1:9001
```

2. **Opc. 3** → Buscar fichero `ejemplo.txt`

Si Peer 1 compartió `/ejemplo.txt` antes, aquí obtendrá:
```csharp
[INFO …] [Peer] Buscando 'ejemplo.txt' en 1 nodos...
✅ Fitxer trobat en els següents nodes:
   • 127.0.0.1:9001
```

3. **Opc. 4** → Descargar desde Peer 1

Indica IP `127.0.0.1`, puerto `9001`, fichero `ejemplo.txt`.

Obtendrás:
```csharp
[INFO …] [Peer] Iniciando descarga de 'ejemplo.txt' desde 127.0.0.1:9001...
[INFO …] Descargado 'ejemplo.txt' desde 127.0.0.1:9001 → downloads/ejemplo.txt
```

4. **Opc. 6** → Ver archivos locales (en `shared_files/` de Peer 2).

Si no ha compartido nada, estará vacío. El descargado queda en `downloads/`.

5. **Opc. 7** → Salir.

## 4. Arrancar Peer 3 (terminal D) sin usar Bootstrap
```bash
cd distrishare
python3 -m cli.main 9003
```
Verás en consola algo como:
```csharp
[INFO …] Peer inicializado en 127.0.0.1:9003
```

Tras ~5 segundos, recibirá por multicast al menos el HELLO de Peer 1 y, si Peer 2 ya estaba encendido, también el HELLO de Peer 2:
```less
[INFO …] [Multicast] Nuevo peer descubierto: ('127.0.0.1', 9001)
[INFO …] [Peer] Añadido vía multicast → ('127.0.0.1', 9001)
[INFO …] [Multicast] Nuevo peer descubierto: ('127.0.0.1', 9002)
[INFO …] [Peer] Añadido vía multicast → ('127.0.0.1', 9002)
```

En este punto, sin haber tocado el Bootstrap, Peer 3 ya conoce a Peer 1 y Peer 2.


