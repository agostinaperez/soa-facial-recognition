# Servicio 2: POST /api/v1/detections.
# Recibe imagen + metadatos (multipart), guarda en BD, sube a SeaweedFS,
# encola inferencia en Celery y retorna frame_id inmediatamente.
import asyncio
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
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
    
    # verifica que extra_metadata sea un JSON válido, si no lo es lanza un error 400    
    try:
        metadata_dict = json.loads(extra_metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El campo extra_metadata debe ser un JSON válido")
    
    image_bytes = await file.read()
    
    # Delegar la subida (E/S síncrona) a un hilo secundario para evitar 
    # bloquear el Event Loop principal de FastAPI durante la transferencia.
    seaweed_fid = await asyncio.to_thread(
        upload_image, image_bytes, file.filename or "image.jpg"
    )

    # Crear registro en BD con estado inicial
    frame = Frame(
        model_id=model_id,
        latitude=latitude,
        longitude=longitude,
        extra_metadata=json.loads(metadata_dict),
        image_url=seaweed_fid,
    )
    db.add(frame)
    db.commit()
    # Actualiza la instancia de frame con el ID generado por la BD tras el commit
    db.refresh(frame)
    
    # Se envía un mensaje (ticket) a Redis usando el método .delay().
    # El Worker de Celery tomará esta tarea en segundo plano usando únicamente el 'frame.id'.
    run_inference.delay(frame.id)

    return {
        "frame_id": frame.id,
        "message": f"Imagen recibida, tu ID es {frame.id}",
    }
