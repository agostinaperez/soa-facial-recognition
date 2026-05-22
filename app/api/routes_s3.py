#Servicio 3: GET /api/v1/frames/{frame_id}.
#Recupera una imagen desde SeaweedFS asociada a un fotograma.
#Soporta redimensión opcional con ?thumbnail=true.
import asyncio
from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from PIL import Image
from sqlalchemy.orm import Session

from database.session import get_db
from models.entities import Frame
from services.seaweed_ds import get_image

router = APIRouter()


@router.get("/frames/{frame_id}")
async def get_frame_image(
    frame_id: int,
    thumbnail: bool = Query(False),
    db: Session = Depends(get_db),
) -> Response:
    #busco si existe un frame con ese id, si no existe tiro un error 404
    frame = db.query(Frame).filter(Frame.frameId == frame_id).first()
    if not frame:
        raise HTTPException(status_code=404, detail="Frame no encontrado")

    try:
        #llama a la funcion de get_image de seaweed_ds, que hace la consulta a seaweedFS, y devuelve los bytes de la imagen, esto se hace de forma asincrona con to_thread para no bloquear el hilo principal
        image_bytes = await asyncio.to_thread(get_image, frame.image_url)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404, detail="Imagen no encontrada en SeaweedFS"
            )
        raise HTTPException(
            status_code=502, detail="Error al comunicarse con SeaweedFS"
        )
    #si le tire el parametro thumbnail=true, redimensiono la imagen a 256x256, para eso uso PIL, abro la imagen con BytesIO, le aplico el metodo thumbnail, y luego guardo la imagen redimensionada en un buffer de bytes, y obtengo los bytes de la imagen redimensionada
    if thumbnail:
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail((256, 256))
        buf = BytesIO()
        format_name = img.format or "JPEG"
        img.save(buf, format=format_name)
        image_bytes = buf.getvalue()

    media_type = "image/jpeg"
    if frame.image_url.lower().endswith(".png"):
        media_type = "image/png"

    return Response(content=image_bytes, media_type=media_type)
