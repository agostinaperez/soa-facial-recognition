
# Servicio de integración con Ultralytics YOLO.
#quiero seguir chequeando este
import os
from io import BytesIO
from pathlib import Path

from PIL import Image

WEIGHTS_DIR = os.getenv("YOLO_WEIGHTS_DIR", "./weights")


def get_available_models() -> list[str]:
    # Escanea el directorio de pesos (./weights/ por defecto) y devuelve una lista con los nombres de archivos .pt encontrados.
    p = Path(WEIGHTS_DIR)
    if not p.exists():
        return []
    return sorted(f.name for f in p.iterdir() if f.suffix == ".pt")


def predict(model_id: str, image_bytes: bytes) -> list[dict]:

    # Ejecuta inferencia YOLO sobre una imagen.
    # model_id: nombre del archivo .pt (ej: yolov8n.pt)
    # image_bytes: contenido binario de la imagen

    # devuelve una lista de detecciones, cada una con: class_name, confidence, bounding_box (x1, y1, x2, y2).    
    from ultralytics import YOLO
    #esto es muy onda lo q hizo el profe en clase
    model = _load_model(model_id)
    img = Image.open(BytesIO(image_bytes))
    results = model(img)
    detections: list[dict] = []
    for r in results:
        for box in r.boxes:
            detections.append(
                {
                    "class_name": model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bounding_box": {
                        "x1": float(box.xyxy[0][0]),
                        "y1": float(box.xyxy[0][1]),
                        "x2": float(box.xyxy[0][2]),
                        "y2": float(box.xyxy[0][3]),
                    },
                }
            )
    return detections

# Los modelos se cachean en memoria para evitar recargarlos en cada inferencia.
_MODEL_CACHE: dict[str, object] = {}


def _load_model(model_id: str):

    # Carga un modelo YOLO desde disco con cache.
    # Si el modelo ya fue cargado previamente retorna la instancia cacheada.

    if model_id not in _MODEL_CACHE:
        from ultralytics import YOLO

        model_path = os.path.join(WEIGHTS_DIR, model_id)
        _MODEL_CACHE[model_id] = YOLO(model_path)
    return _MODEL_CACHE[model_id]
