# SOA Face Detection

Sistema de análisis de fotogramas e inferencia con YOLO, expuesto mediante APIs REST.

## Stack

- FastAPI (Python 3.10+) — framework web
- SQLAlchemy — ORM para MySQL
- Celery + Redis — cola de tareas asincrónicas
- Ultralytics (YOLOv8) — inferencia de detección facial
- SeaweedFS — almacenamiento de objetos distribuido
- Docker Compose — infraestructura (MySQL, Redis, SeaweedFS)

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
# 1. Variables de entorno
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

## API endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/models` | Lista modelos `.pt` disponibles |
| `POST` | `/api/v1/detections` | Envía imagen para detección (multipart) |
| `GET` | `/api/v1/frames/{id}` | Obtiene imagen de un fotograma |
| `GET` | `/api/v1/frames/search` | Búsqueda con filtros |

### POST /detections

```bash
curl -X POST http://localhost:8000/api/v1/detections \
  -F "file=@foto.jpg" \
  -F "model_id=yolov8n.pt" \
  -F "latitude=-34.6037" \
  -F "longitude=-58.3816" \
  -F 'extra_metadata={"source":"camara1","lugar":"puerta_principal"}'
```

### GET /frames/search

```
GET /api/v1/frames/search?min_lat=-35&max_lat=-34&detected_class=person
```

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
