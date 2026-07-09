# SOA Face Detection

Sistema de análisis de fotogramas e inferencia con YOLO, expuesto mediante APIs REST.

## Stack

- FastAPI (Python 3.10+) — framework web
- SQLAlchemy — ORM para MySQL
- Celery + Redis — cola de tareas asincrónicas
- Ultralytics (YOLOv8) — inferencia de detección facial
- SeaweedFS — almacenamiento de objetos distribuido
- Docker Compose — infraestructura (MySQL, Redis, SeaweedFS)
- Keycloak para protección de endpoints

## Arquitectura

```
API recibe imagen (POST /detections)
  → guarda en SeaweedFS
  → escribe registro "En Proceso" en MySQL
  → encola ticket en Redis (broker Celery)
  → responde al usuario: "Imagen recibida, ID = X"

Celery Worker (segundo plano)
  → toma ticket de Redis
  → descarga imagen de SeaweedFS
  → ejecuta YOLO (Ultralytics)
  → guarda detecciones en MySQL
```

## Requisitos

- Python 3.10+
- Docker y Docker Compose
- Pesos YOLO (`.pt`) — descargar y colocar en `./weights/`

## Setup rápido

```bash
cp .env.example .env

# 2. Infraestructura (MySQL, Redis, SeaweedFS)
docker compose up -d

# 3. Dependencias Python
pip install -r requirements.txt

# 4. Pesos de YOLO
# Descargar yolov8n.pt desde https://github.com/ultralytics/assets/releases
# y colocarlo en ./weights/

# 5. Iniciar API
uvicorn app.main:app --reload --port 8000

# 6. En otra terminal, iniciar worker
celery -A app.worker.tasks worker --loglevel=info
```

Keycloak se configura automáticamente (~60s). Consola: `http://localhost:8081` (`admin`/`admin`).
Usuarios creados: `admin/admin123`, `operator/operator123`, `viewer/viewer123`.

## Escalado de contenedores
 El sistema cuenta con la posibilidad de aumentar el numero de workers, volumenes de almacenamiento de archivos y apis ejecutandose. El siguiente comando le permitira escalar la cantidad de cada uno segun desee:
 ```bash
 docker compose up -d --scale seaweed_volume=<n° volumenes de seaweed> --scale worker=<n° workers> --scale api=<n° apis>
 ```

## Endpoints

| Método | Ruta | Roles |
|---|---|---|
| `GET` | `/api/v1/models` | admin, operator, viewer |
| `POST` | `/api/v1/detections` | admin, operator |
| `GET` | `/api/v1/frames/{id}` | admin, operator, viewer |
| `GET` | `/api/v1/frames/search` | admin, operator, viewer |
| `POST` | `/api/v1/persons` | admin, operator |
| `GET` | `/api/v1/persons/{id}` | admin, operator, viewer |
| `POST` | `/api/v1/persons/{id}/embeddings` | admin, operator |
| `POST` | `/api/v1/face-recognition` | admin, operator |
| `POST` | `/api/v1/auth/face/login` | público |
| `GET` | `/api/v1/auth/me` | admin, operator, viewer |

## Comandos

```bash
uvicorn app.main:app --reload --port 8000   # API dev
celery -A app.worker.tasks worker --loglevel=info  # Worker
docker compose up -d                         # Infraestructura
docker compose down                          # Parar infra
```

## Testing con Bruno

[Bruno](https://www.usebruno.com) es un cliente API open-source que guarda las colecciones como archivos de texto directamente en el repo (sin cuenta en la nube).

### Instalación

```bash
# Opción A — App de escritorio (recomendado)
# Descargar desde: https://www.usebruno.com/downloads

# Opción B — CLI
npm install -g @usebruno/cli
```

### Abrir la colección

1. Abrir Bruno desktop
2. **File > Open Collection**
3. Seleccionar la carpeta `./bruno/` del repo
4. En el selector de entorno (arriba a la derecha) elegir **local**
