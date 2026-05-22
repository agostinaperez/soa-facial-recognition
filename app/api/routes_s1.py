
# Servicio 1: GET /api/v1/models
from fastapi import APIRouter

from services.yolo_core import get_available_models

router = APIRouter()


@router.get("/models")
def list_models() -> list[str]:

    # Escanea YOLO_WEIGHTS_DIR y devuelve
    # los nombres de archivos .pt encontrados.
    return get_available_models()
