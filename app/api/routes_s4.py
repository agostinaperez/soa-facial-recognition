
#Servicio 4: GET /api/v1/frames/search
# Búsqueda dinámica de fotogramas con filtros opcionales.
# - min_lat / max_lat: Filtra por rango de latitud.
# - min_lon / max_lon: Filtra por rango de longitud.
# - detected_class: JOIN con Detection y filtra por clase.
# - metadata_key / metadata_value: Filtra dentro del JSON
#   extra_metadata usando el operador JSON de MySQL
#   (JSON_EXTRACT vía SQLAlchemy).

# Todos los filtros son opcionales y combinables. Si no se envía ningún filtro, devuekve todos los frames.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.entities import Detection, Frame
from app.schemas.dtos import FrameResponse

router = APIRouter()


@router.get("/frames/search", response_model=list[FrameResponse])
def search_frames(
    min_lat: float = Query(None),
    max_lat: float = Query(None),
    min_lon: float = Query(None),
    max_lon: float = Query(None),
    detected_class: str = Query(None),
    metadata_key: str = Query(None),
    metadata_value: str = Query(None),
    db: Session = Depends(get_db),
) -> list[Frame]:
    
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

    # Filtro por campo JSON extra_metadata
    if metadata_key is not None and metadata_value is not None:
        query = query.filter(
            Frame.extra_metadata[metadata_key].as_string() == metadata_value
        )

    return query.all()
