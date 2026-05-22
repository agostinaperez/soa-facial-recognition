
# Configuración de Celery y tareas asincrónicas.
import os

from celery import Celery

from database.session import SessionLocal
from models.entities import Detection
from services.seaweed_ds import get_image
from services.yolo_core import predict

# URL de Redis usada como broker y backend de resultados
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
# Instancia de la aplicación Celery
celery_app = Celery("soa_worker", broker=BROKER_URL, backend=BROKER_URL)


@celery_app.task
def run_inference(frame_id: str) -> dict:
    """Ejecuta la inferencia de detección de objetos vía YOLO sobre un frame específico.

    Esta tarea en segundo plano encapsula el pipeline analítico completo:
    1. Obtiene la metadata y el modelo objetivo desde el repositorio relacional (MySQL).
    2. Descarga el archivo binario del frame desde el almacenamiento de objetos (SeaweedFS).
    3. Ejecuta el motor de inferencia de redes neuronales (YOLO Core).
    4. Persiste los resultados estructurados (bounding boxes) en la base de datos.

    Args:
        frame_id (str): Identificador único global (UUID) del fotograma a procesar.

    Returns:
        Dict[str, Any]: Resumen de la ejecución que contiene el ID del frame 
                        y la cantidad total de objetos detectados.

    Raises:
        Exception: Si ocurre un fallo de red, transaccional o en la inferencia del 
                   modelo. Genera un rollback automático de la transacción.
    """

    db = SessionLocal()
    try:
        from models.entities import Frame

        # Buscar el fotograma en BD
        frame = db.query(Frame).filter(Frame.frameId == frame_id).first()
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
                    frame_id=frame.frameId,
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
