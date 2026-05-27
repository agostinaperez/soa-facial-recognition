import base64

import face_recognition as fr
import numpy as np

from database.session import SessionLocal
from models.entities import Detection, Embedding, EmbeddingTask, Person
from services.face_embedder import generate_face_embedding
from services.faiss_index import build_index, search as faiss_search
from services.seaweed_ds import get_image
from worker.celery_app import celery_app


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
        from services.yolo_core import predict

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


@celery_app.task
def generate_embeddings_task(person_id: str, task_ids: list[str]) -> dict:
    """Genera embeddings faciales para cada tarea encolada

    Por cada taskId:
    1. Busca el EmbeddingTask en DB.
    2. Descarga la imagen desde SeaweedFS.
    3. Genera el embedding con face_recognition.
    4. Persiste el vector en la tabla embeddings.
    5. Actualiza el estado a Completado / Fallido.
    """
    db = SessionLocal()
    try:
        for task_id in task_ids:
            task = db.query(EmbeddingTask).filter(EmbeddingTask.taskId == task_id).first()
            if not task:
                continue
            try:
                image_bytes = get_image(task.seaweed_fid)
                vector = generate_face_embedding(image_bytes)
                if vector is None:
                    task.status = "Fallido"
                else:
                    db.add(Embedding(personId=person_id, vector=vector))
                    task.status = "Completado"
            except Exception:
                task.status = "Fallido"
        db.commit()
        return {"person_id": person_id, "tasks_processed": len(task_ids)}
    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


@celery_app.task(name="worker.tasks.face_recognition_task")
def face_recognition_task(image_b64: str, threshold: float) -> dict:
    """Reconoce una persona a partir de una imagen comparando contra embeddings almacenados.

    1. Decodifica la imagen y genera su embedding facial.
    2. Carga todos los embeddings de la BD.
    3. Calcula distancias euclídeas y selecciona el mejor candidato.
    4. Retorna la persona si confidence >= threshold, o resultado negativo si no.
    """
    image_bytes = base64.b64decode(image_b64)
    query_vector = generate_face_embedding(image_bytes)

    if query_vector is None:
        return {"error": "no_face", "detail": "No se detectó ningún rostro en la imagen"}

    db = SessionLocal()
    try:
        stored_embeddings = db.query(Embedding).all()
        if not stored_embeddings:
            return {"personId": None, "confidence": 0.0}

        # Separamos vectores y personIds en listas paralelas.
        # La posición i en vectors corresponde al personId en la posición i de person_ids_list.
        vectors = [emb.vector for emb in stored_embeddings]
        person_ids_list = [emb.personId for emb in stored_embeddings]

        # Construimos el índice FAISS en memoria con todos los embeddings de la BD.
        # El índice se reconstruye en cada llamada para garantizar consistencia con MySQL.
        index, pid_list = build_index(vectors, person_ids_list)

        # Buscamos el vecino más cercano al query_vector dentro del índice FAISS.
        results = faiss_search(index, pid_list, query_vector, k=1)

        best_person_id, l2_sq_dist = results[0]

        # IndexFlatL2 devuelve distancia L2 al cuadrado (no la euclídea directa).
        # Aplicamos sqrt para obtener la distancia euclídea equivalente a face_distance(),
        # y luego calculamos confidence como 1 - distancia (igual que antes).
        confidence = max(0.0, 1.0 - float(np.sqrt(l2_sq_dist)))

        if confidence >= threshold:
            person = db.query(Person).filter(Person.personId == best_person_id).first()
            return {
                "personId": person.personId,
                "nombre": person.nombre,
                "apellido": person.apellido,
                "confidence": round(confidence, 4),
            }

        return {"personId": None, "confidence": round(confidence, 4)}
    finally:
        db.close()
