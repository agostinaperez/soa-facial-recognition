
#DTOs para serialización de requests/responses.

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class DetectionResponse(BaseModel):
    
    # DTO para serializar una detección individual.
    id: str
    class_name: str
    confidence: float
    bounding_box: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class FrameResponse(BaseModel):

    # DTO para serializar un fotograma completo con su lista de detecciones anidadas.

    id: str
    model_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    extra_metadata: Optional[dict[str, Any]] = None
    image_url: str
    created_at: datetime
    detections: list[DetectionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class FrameCreateResponse(BaseModel):
    # DTO para la respuesta inmediata del POST /detections.
    # Se devuelve antes de que el worker termine la inferencia.

    frame_id: str
    message: str
