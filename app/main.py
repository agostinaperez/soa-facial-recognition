
#Punto de entrada de la app FastAPI.
#Inicializa la app, monta los routers y crea las tablas en la db.

from fastapi import FastAPI

from app.api.routes_s1 import router as s1_router
from app.api.routes_s2 import router as s2_router
from app.api.routes_s3 import router as s3_router
from app.api.routes_s4 import router as s4_router
from app.api.routes_s5 import router as s5_router
from app.database.session import Base, engine

app = FastAPI(
    title="SOA Face Detection API",
    version="1.0.0",
    description="API REST para detección facial con YOLO, "
    "procesamiento asincrónico con Celery y almacenamiento en SeaweedFS.",
)

# Montar todos los routers bajo el prefijo /api/v1
app.include_router(s1_router, prefix="/api/v1", tags=["Models"])
app.include_router(s2_router, prefix="/api/v1", tags=["Detections"])
app.include_router(s4_router, prefix="/api/v1", tags=["Frames"])
app.include_router(s5_router, prefix="/api/v1", tags=["Persons"])
app.include_router(s3_router, prefix="/api/v1", tags=["Frames"])


@app.on_event("startup")
def on_startup() -> None:
    
    # Crea las tablas en MySQL al iniciar la aplicación
    Base.metadata.create_all(bind=engine)
