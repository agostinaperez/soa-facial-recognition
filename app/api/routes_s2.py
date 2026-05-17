# Servicio 2: POST /api/v1/detections.
# Recibe imagen + metadatos (multipart), guarda en BD, sube a SeaweedFS,
# encola inferencia en Celery y retorna frame_id inmediatamente.
import asyncio
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.entities import Frame
from app.schemas.dtos import FrameCreateResponse
from app.services.seaweed_ds import upload_image
from app.worker.tasks import run_inference

router = APIRouter()


@router.post("/detections", response_model=FrameCreateResponse, status_code=201)
async def create_detection(
    file: UploadFile = File(...),
    model_id: str = Form(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
    extra_metadata: str = Form("{}"),
    db: Session = Depends(get_db),
) -> dict:
    
    image_bytes = await file.read()
    #esto ejecuta la funcion de forma asincrona el otro hilo, es to_thread(funcion, argumentos), devuelve la url de la imagen
    seaweed_fid = await asyncio.to_thread(
        upload_image, image_bytes, file.filename or "image.jpg"
    )

    # Crear registro en BD con estado inicial
    frame = Frame(
        model_id=model_id,
        latitude=latitude,
        longitude=longitude,
        extra_metadata=json.loads(extra_metadata),
        image_url=seaweed_fid,
    )
    db.add(frame)
    db.commit()
    db.refresh(frame)

    # Encolar tarea de inferencia en Celery
    run_inference.delay(frame.id)

    return {
        "frame_id": frame.id,
        "message": "Imagen recibida, tu ID es X",
    }
