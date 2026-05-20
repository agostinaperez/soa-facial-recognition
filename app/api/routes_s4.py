
#Servicio 4: GET /api/v1/frames/search
# Búsqueda dinámica de fotogramas con filtros opcionales.
# - min_lat / max_lat: Filtra por rango de latitud.
# - min_lon / max_lon: Filtra por rango de longitud.
# - detected_class: JOIN con Detection y filtra por clase.
# - metadata_key / metadata_value: Filtra dentro del JSON
#   extra_metadata usando el operador JSON de MySQL
#   (JSON_EXTRACT vía SQLAlchemy).

# Todos los filtros son opcionales y combinables. Si no se envía ningún filtro, devuekve todos los frames.

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.entities import Detection, Frame
from app.schemas.dtos import FrameSearchResponse, DetectionResponse

router = APIRouter()


@router.get("/frames/search", response_model=list[FrameSearchResponse])
def search_frames(
    request: Request,
    min_lat: float = Query(None),
    max_lat: float = Query(None),
    min_lon: float = Query(None),
    max_lon: float = Query(None),
    detected_class: str = Query(None),
    metadata_key: list[str] = Query(None),
    metadata_value: list[str] = Query(None),
    db: Session = Depends(get_db),
) -> list[Frame]:

    if metadata_key and metadata_value and len(metadata_key) != len(metadata_value):
        raise HTTPException(
            status_code=422,
            detail="metadata_key y metadata_value deben tener la misma cantidad de elementos",
        )

    query = db.query(Frame)

    # Filtro por rango de latitud
    if min_lat is not None and max_lat is not None:
        query = query.filter(
            Frame.latitude >= min_lat,
            Frame.latitude <= max_lat,
        )

    # Filtro por rango de longitud
    if min_lon is not None and max_lon is not None:
        query = query.filter(
            Frame.longitude >= min_lon,
            Frame.longitude <= max_lon,
        )

    # Filtro por clase detectada (INNER JOIN con Detection)
    if detected_class:
        query = query.join(Detection).filter(
            Detection.class_name == detected_class
        )

    # Filtro por uno o varios pares clave/valor dentro del JSON extra_metadata
    if metadata_key and metadata_value:
        for key, value in zip(metadata_key, metadata_value):
            query = query.filter(
                Frame.extra_metadata[key].as_string() == value
            )
    frames = query.all()
    result = []
    for frame in frames:
        result.append(FrameSearchResponse(
            frameId = frame.id,
            imageURL=str(request.base_url) + f"api/v1/frames/{frame.id}",
            metadata = frame.extra_metadata,
            detections = [DetectionResponse.model_validate(d) for d in frame.detections]
        ))
    return result

