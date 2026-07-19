
#Punto de entrada de la app FastAPI.
#Inicializa la app, monta los routers y crea las tablas en la db.

from sqlalchemy.exc import OperationalError, DatabaseError

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routes_s1 import router as s1_router
from api.routes_s2 import router as s2_router
from api.routes_s3 import router as s3_router
from api.routes_s4 import router as s4_router
from api.routes_s5 import router as s5_router
from api.routes_srps import router as srps_router
from database.session import Base, engine
from routes_auth import router as auth_router

import os
import socket
import time
from statsd import StatsClient

TELEGRAF_HOST = os.getenv("TELEGRAF_HOST", "telegraf")
TELEGRAF_PORT = int(os.getenv("TELEGRAF_PORT", 8125))

app = FastAPI(
    title="SOA Face Detection API",
    version="1.0.0",
    description="API REST para deteccion facial con YOLO, "
    "procesamiento asincronico con Celery y almacenamiento en SeaweedFS.",
    swagger_ui_init_oauth={
        "clientId": "soa",
        "appName": "SOA Face Detection",
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Obtener el nombre del contenedor para usarlo como prefijo en las métricas
container_id = socket.gethostname()

# Inicializar el cliente de StatsD con el prefijo del contenedor
statsd = StatsClient(host=TELEGRAF_HOST, port=TELEGRAF_PORT, prefix=f'api.{container_id}')

# Middleware para monitoreo de throughput, latencia y errores
@app.middleware("http")
async def monitor_metrics_middleware(request: Request, call_next):
    # Throughput: Contamos que entró una petición a esta instancia específica
    statsd.incr('throughput.incoming')
    
    # Contador por servicio consultado
    endpoint_path = request.url.path.strip("/").replace("/", "_")
    
    # Si la ruta quedó vacía (la raíz del sitio "/"), le asignamos por defecto el nombre "root"
    if not endpoint_path:
        endpoint_path = "root"
        
    # Incrementamos el contador específico de este endpoint
    statsd.incr(f'endpoint.{endpoint_path}.queries')
    
    start_time = time.time()
    
    # Procesar la petición (va al endpoint correspondiente)
    response = await call_next(request)
    
    # Latencia: Calculamos cuánto tardó en milisegundos
    duration = (time.time() - start_time) * 1000
    statsd.timing('latency', duration)
    
    # Throughput exitoso vs errores
    if response.status_code == 200:
        statsd.incr('throughput.success')
    elif response.status_code >= 400:
        statsd.incr(f'errors.{response.status_code}')
        
    return response

app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(s1_router, prefix="/api/v1", tags=["Models"])
app.include_router(s2_router, prefix="/api/v1", tags=["Detections"])
app.include_router(s4_router, prefix="/api/v1", tags=["Frames"])
app.include_router(s5_router, prefix="/api/v1", tags=["Persons"])
app.include_router(s3_router, prefix="/api/v1", tags=["Frames"])
app.include_router(srps_router, prefix="/api/v1", tags=["Rock Paper Scissors"])


@app.on_event("startup")
def on_startup() -> None:
    
    # Crea las tablas en MySQL al iniciar la aplicación
    retries = 5
    while retries > 0:
        try:
            print("Intentando crear y sincronizar tablas en MySQL...")
            # Crea las tablas en MySQL al iniciar la aplicación
            Base.metadata.create_all(bind=engine)
            print("¡Conexión exitosa a MySQL y tablas sincronizadas correctamente!")
            break
        except (OperationalError, DatabaseError) as e:
            retries -= 1
            print(f"MySQL no responde aún ({retries} reintentos restantes)... Esperando 3 segundos.")
            time.sleep(3)
            
    if retries == 0:
        print("ERROR CRÍTICO: No se pudo conectar a MySQL tras varios intentos.")
        raise RuntimeError("No se pudo establecer conexión con la base de datos MySQL.")


@app.get("/health", tags=["Monitoreo"])
def health_check():
    # Endpoint de uso interno para el Healthcheck
    return {"status": "ok"}
