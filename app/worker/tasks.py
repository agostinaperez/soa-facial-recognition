
# Configuración de Celery y tareas asincrónicas.
import os

from celery import Celery

from app.database.session import SessionLocal
from app.models.entities import Detection
from app.services.seaweed_ds import get_image
from app.services.yolo_core import predict

# URL de Redis usada como broker y backend de resultados
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Instancia de la aplicación Celery
celery_app = Celery("soa_worker", broker=REDIS_URL, backend=REDIS_URL)


@celery_app.task
def run_inference(frame_id: str) -> dict:

    # Ejecuta inferencia YOLO sobre el frame.
    db = SessionLocal()
    try:
        from app.models.entities import Frame

        # Buscar el fotograma en BD
        frame = db.query(Frame).filter(Frame.id == frame_id).first()
        if not frame:
            return {"error": "Frame no encontrado"}

        # Descargar imagen desde SeaweedFS por fid
        image_bytes = get_image(frame.image_url)

        # Ejecutar inferencia YOLO
        detections = predict(frame.model_id, image_bytes)

        # Persistir cada detección en BD
        for det in detections:
            db.add(
                Detection(
                    frame_id=frame.id,
                    class_name=det["class_name"],
                    confidence=det["confidence"],
                    bounding_box=det["bounding_box"],
                )
            )
        db.commit()

        return {"frame_id": frame_id, "detections_count": len(detections)}

    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()
